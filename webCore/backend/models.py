
import sanic, time, asyncio, uuid, threading
import sanic.response
from sanic import HTTPResponse
# Internal Classes
from webCore.auth import protected, multi_protected

modelsAPIWebObj = sanic.Blueprint("modelsAPIWebObj", url_prefix="/models")
client_progress = {}


@modelsAPIWebObj.route("/getmodels", methods=["GET"])
@protected
async def modelsAPIWebObj_getmodels(request) -> HTTPResponse:

    res = await request.ctx.databaseObj.getModels()
    print(f"[INFO] Gathered models ==> {res}")
    if type(res) == list:
        return sanic.response.json({"status": True, "provider": request.ctx.configObj.model_type, "data": res})
    else:
        return sanic.response.json({"status": False, "message": res["message"]})



@modelsAPIWebObj.route("/generate", methods=["POST"])
@multi_protected
async def modelsAPIWebObj_generate(request) -> HTTPResponse:
    jsondata = request.json
    if not jsondata:
        return sanic.response.json({"status": False, "message": "Invalid input"}, status=400)
    
    if not request.ctx.authSessionObj:
        # get non authed temp data
        if "topic" not in jsondata:
            return sanic.response.json({"status": False, "message": "Connot just prompt normally."})

        else:
            genRes = request.ctx.modelObj.generate_response(request.ctx.toolkitObj.pharsePrompt(jsondata["topic"], jsondata["cardCount"]), jsondata["model"] )

            if genRes:
                pharsedRes = request.ctx.toolkitObj.parseGeneratedResponse(genRes)

                if pharsedRes:
                    return sanic.response.json({"status": True, "message": pharsedRes})
            return sanic.response.json({"status": False, "message": "Unkown error happend while generating."})
    else:
        if "topic" not in jsondata:
            genRes = request.ctx.modelObj.generate_response(jsondata["prompt"], jsondata["model"])
            if genRes:
                return sanic.response.json({"status": True, "message": genRes})
            return sanic.response.json({"status": False, "message": "Unkown error happend while generating."})

        else:
            genRes = request.ctx.modelObj.generate_response(request.ctx.toolkitObj.pharsePrompt(jsondata["topic"], jsondata["cardCount"]), jsondata["model"] )
            if genRes:
                pharsedRes = request.ctx.toolkitObj.parseGeneratedResponse(genRes)

                if pharsedRes:
                    return sanic.response.json({"status": True, "message": pharsedRes})
            return sanic.response.json({"status": False, "message": "Unkown error happend while generating."})


# pull a new model
@modelsAPIWebObj.route("/pull", methods=["POST"])
@protected
async def modelsAPIWebObj_pull(request) -> HTTPResponse:
    """Start model pull and return client ID for progress tracking."""
    jsondata = request.json
    if not jsondata.get("name"):
        return sanic.response.json({"status": False, "message": "Invalid input"}, status=400)
    
    client_id = str(uuid.uuid4())
    
    # start the pull process in a separate thread to avoid blocking
    thread = threading.Thread(
        target=request.ctx.modelObj.pull_new_model_sync,
        args=(jsondata["name"], client_id),
        daemon=True
    )
    thread.start()
    
    # init progress tracking
    client_progress[client_id] = {
        "status": "starting",
        "completed": 0,
        "total": 0,
        "percentage": 0,
        "model": jsondata["name"],
        "timestamp": time.time()
    }
    
    return sanic.response.json({
        "status": True, 
        "message": "Pull started", 
        "client_id": client_id,
        "model": jsondata["name"]
    })

@modelsAPIWebObj.route("/pull/progress/<client_id>", methods=["GET"])
@protected
async def get_pull_progress(request, client_id: str) -> HTTPResponse:
    """get current progress for a pull operation."""
    
    if client_id not in client_progress:
        return sanic.response.json({"status": False, "message": "Invalid client ID or pull not found"}, status=404)
    if client_id not in request.ctx.modelObj.active_pulls:
        return sanic.response.json({"status": False, "message": "Model already pulled or issue pulling model."})

    progress_data = request.ctx.modelObj.active_pulls[client_id]

    return sanic.response.json({"status": True, "data": progress_data})

@modelsAPIWebObj.route("/pull/cancel/<client_id>", methods=["POST"])
@protected
async def cancel_pull(request, client_id: str) -> HTTPResponse:
    """cancel a pull operation."""

    if client_id not in client_progress:
        return sanic.response.json({"status": False, "message": "Invalid client ID or pull not found"}, status=404)
    if client_id not in request.ctx.modelObj.active_pulls:
        return sanic.response.json({"status": False, "message": "Model already pulled or issue pulling model."})

    request.ctx.modelObj.cancel_pull(client_id)
    if client_id in client_progress:
        del client_progress[client_id]
    return sanic.response.json({"status": True, "message": "Pull cancelled successfully."})

async def handle_model_pull(model_obj, model_name: str, client_id: str):
    """Background task to handle model pulling and store progress."""
    try:
        async for progress in model_obj.pull_new_model_stream(model_name, client_id):
            client_progress[client_id] = progress
            
            # if there's an error or completion, we can clean up after some time
            if progress.get("error") or progress.get("status") == "success":
                # keep the final status for a while before cleanup
                await asyncio.sleep(30)
                if client_id in client_progress:
                    del client_progress[client_id]
                break
    except Exception as e:
        client_progress[client_id] = {"error": True, "message": str(e)}



# delete model
@modelsAPIWebObj.route("/delete", methods=["POST"])
@protected
async def modelsAPIWebObj_delete(request) -> HTTPResponse:
    jsondata = request.json
    
    if not jsondata.get("model"):
        return sanic.response.json({"status": False, "message": "Invalid input"}, status=400)

    try:
        model = jsondata["model"]
        res = request.ctx.modelObj.delete_model(model)
        if res["status"]:
            return sanic.response.json({"status": True, "message": "success", "data": res})
        else:
            return sanic.response.json({"status": False, "message": "Error deleting the model"})
    except Exception as e:
        return sanic.response.json({"status": False, "message": "Error deleting the model"})