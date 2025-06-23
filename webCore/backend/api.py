import sanic, asyncio, logging, json
import sanic.response
from sanic import HTTPResponse

from webCore.auth import protected, multi_protected

apiWebObj = sanic.Blueprint("apiWebObj", url_prefix="/api")


# /
@apiWebObj.route("/login", methods=["POST"])
async def apiWebObj_login(request):
    jsondata = json.loads(request.body)
    username = jsondata["username"].lower()
    password = jsondata["password"]
    
    # check data
    if username == "" or password == "":
        return sanic.response.json({"status": False, "message": "Invalid username or password."}, status=400)
    if len(password) < 8:
        return sanic.response.json({"status": False, "message": "Password must be at least 8 characters long."}, status=400)
    if len(username) < 4:
        return sanic.response.json({"status": False, "message": "Username must be at least 4 characters long."}, status=400)
    
    # handle login
    attemptLogin = await request.ctx.databaseObj.attemptUserLogin(request, username, password)

    logging.info(f"[ Login Attempt ] - {username} --> {attemptLogin}")

    if attemptLogin["status"]:
        response = sanic.response.json({"status": True, "message": "User login successfully."}, status=200)
        response.add_cookie(
        	'token', 
        	attemptLogin['data']['token'],
            httponly=request.ctx.configObj.use_https,
            secure=request.ctx.configObj.use_https,
        	samesite='Lax',
        )
        
        return response
    else:
        return sanic.response.json({"status": False, "message": "Invalid username or password."}, status=400)


@apiWebObj.route("/deck/save", methods=["POST"])
@multi_protected
async def apiWebObj_savedeck(request) -> HTTPResponse:
    if not request.ctx.authSessionObj:
        # handle non authed user
        userClientID = request.cookies.get("guest_session_id")
        jsondata = request.json
        if not jsondata:
            return sanic.response.json({"status": False, "message": "Invalid input data."}, status=400)

        # validate required fields
        name = jsondata.get("name")
        decks = jsondata.get("cards")

        if not isinstance(name, str) or not name.strip():
            return sanic.response.json({"status": False, "message": "Field 'name' is required and must be a non-empty string."}, status=400)

        if not isinstance(decks, list) or not decks:
            return sanic.response.json({"status": False, "message": "Field 'cards' must be a non-empty list."}, status=400)

        for i, card in enumerate(decks):
            if not isinstance(card, dict):
                return sanic.response.json({"status": False, "message": f"Card at index {i} must be a dictionary."}, status=400)

            if "front" not in card or "back" not in card:
                return sanic.response.json({"status": False, "message": f"Card at index {i} must have 'front' and 'back'."}, status=400)

            if not isinstance(card["front"], str) or not isinstance(card["back"], str):
                return sanic.response.json({"status": False, "message": f"'front' and 'back' of card at index {i} must be strings."}, status=400)
            

        res = await request.ctx.databaseObj.addTempDeck(
            userClientID, jsondata
        )

        return sanic.response.json(res)

    else:
        jsondata = request.json

        if not jsondata:
            return sanic.response.json({"status": False, "message": "Invalid input data."}, status=400)

        # validate required fields
        name = jsondata.get("name")
        decks = jsondata.get("cards")

        if not isinstance(name, str) or not name.strip():
            return sanic.response.json({"status": False, "message": "Field 'name' is required and must be a non-empty string."}, status=400)

        if not isinstance(decks, list) or not decks:
            return sanic.response.json({"status": False, "message": "Field 'cards' must be a non-empty list."}, status=400)

        for i, card in enumerate(decks):
            if not isinstance(card, dict):
                return sanic.response.json({"status": False, "message": f"Card at index {i} must be a dictionary."}, status=400)

            if "front" not in card or "back" not in card:
                return sanic.response.json({"status": False, "message": f"Card at index {i} must have 'front' and 'back'."}, status=400)

            if not isinstance(card["front"], str) or not isinstance(card["back"], str):
                return sanic.response.json({"status": False, "message": f"'front' and 'back' of card at index {i} must be strings."}, status=400)
            

        res = await request.ctx.databaseObj.addDeck(
            request.ctx.authSessionObj["authTraveler"], jsondata
        )

        return sanic.response.json(res)

    
@apiWebObj.route("/decks/get", methods=["GET"])
@multi_protected
async def apiWebObj_getdecks(request) -> HTTPResponse:
    if not request.ctx.authSessionObj:
        # get non authed temp data
        res = await request.ctx.databaseObj.getTempDecksByClientID(
            request.cookies.get("guest_session_id")
        )

        if res["status"]:
            return sanic.response.json(res)
        else:
            return sanic.response.json({"status": False, "message": res["message"]})
    else:
        res = await request.ctx.databaseObj.getDecksByUserID(
            request.ctx.authSessionObj["authTraveler"]
        )
        if res["status"]:
            return sanic.response.json(res)
        else:
            return sanic.response.json({"status": False, "message": res["message"]})


@apiWebObj.route("/decks/delete", methods=["DELETE"])
@multi_protected
async def apiWebObj_deldeck(request) -> HTTPResponse:
    jsondata = request.json  

    if not jsondata:
        return sanic.response.json({"status": False, "message": "Invalid input data."}, status=400)

    if not request.ctx.authSessionObj:
        # get non authed temp data
        userClientID = request.cookies.get("guest_session_id")

        res = await request.ctx.databaseObj.delDeck(
            jsondata["deckID"],
            True
        )
        if res["status"]:
            return sanic.response.json(res)
        else:
            return sanic.response.json({"status": False, "message": res["message"]})
    else:
        res = await request.ctx.databaseObj.delDeck(
            jsondata["deckID"],
            False
        )
        if res["status"]:
            return sanic.response.json(res)
        else:
            return sanic.response.json({"status": False, "message": res["message"]})


@apiWebObj.route("/settings", methods=["GET", "POST"])
@protected
async def apiWebObj_csonfig(request) -> HTTPResponse:
    if request.method == "GET":
        return sanic.response.json(request.ctx.configObj.export_as_dict())

    elif request.method == "POST":
        jsonData = request.json
        currentConfig = request.ctx.configObj.export_as_dict()
        changes_made = False

        for section, items in jsonData.items():
            for key, new_value in items.items():
                current_value = currentConfig.get(section, {}).get(key)

                if str(current_value) != str(new_value):
                    request.ctx.configObj.set(section, key, str(new_value))
                    changes_made = True

        if changes_made:
            request.ctx.configObj.save()
            return sanic.response.json({"status": True, "message": "Settings updated successfully."})
        else:
            return sanic.response.json({"status": True, "message": "No changes detected."})

    return sanic.response.json({"status": False, "message": "Invalid request type"})


@apiWebObj.route("/settings/export", methods=["GET"])
@protected
async def apiWebObj_exportSettings(request) -> HTTPResponse:

    getSettingsAsDict = request.ctx.configObj.export_as_dict()
    if getSettingsAsDict:
        return sanic.response.json(getSettingsAsDict)
    else:
        return sanic.response.json({"status": False, "message": "Issue gathering the config data as a json file."})

@apiWebObj.route("/users", methods=["GET", "POST", "DELETE"])
@protected
async def apiWebObj_users(request) -> HTTPResponse:
    if request.method == "GET":
        return sanic.response.json(await request.ctx.databaseObj.getAllUsers())
    
    elif request.method == "POST":
        reqData = request.json

        res = await request.ctx.databaseObj.addNewUser(reqData["username"], reqData["password"], reqData["role"])
        
        if res["status"]:
            return sanic.response.json({"status": True, "message": f"User {reqData['username']} has been created."})
        else:
            return sanic.response.json({"status": False, "message": "Failed to create new user."})
        
    elif request.method == "DELETE":
        
        reqData = request.json or {}

        userID = reqData.get("userID")
        if not userID:
            return sanic.response.json({"status": False, "message": "Missing 'userID' in request."}, status=400)

        res = await request.ctx.databaseObj.deleteUser(userID)
        if res["status"]:
            return sanic.response.json({"status": True, "message": f"User {userID} has been deleted."})
        else:
            return sanic.response.json({"status": False, "message": f"Failed to delete user: {res.get('message', 'Unknown error')}."})
        

@apiWebObj.route("/system/restart", methods=["POST"])
@protected
async def apiWebObj_restart(request) -> HTTPResponse:
    try:
        reqData = request.json
        service_name = reqData.get("service")
        
        if service_name not in ["zapcards", "ollama"]:
            return sanic.response.json({
                "status": False, 
                "message": "Invalid service"
            })

        logging.info(f"Restarting service ==> {service_name}")
        
        # Check if running in Docker
        is_docker = await request.ctx.toolkitObj.check_docker_container()
        print(f"is docker ==> {is_docker}")

        if is_docker:
            logging.info(f"Service {service_name} detected as Docker container")
            success, stdout, stderr = await request.ctx.toolkitObj.restart_docker_container(service_name)
            restart_method = "Docker container"
        else:
            logging.info(f"Service {service_name} detected as systemd service")
            success, stdout, stderr = await request.ctx.toolkitObj.restart_systemd_service(service_name)
            restart_method = "systemd service"
        
        if success:
            return sanic.response.json({
                "status": True,
                "message": f"Service restart initiated via {restart_method}.",
                "method": "docker" if is_docker else "systemd"
            })
        else:
            return sanic.response.json({
                "status": False,
                "message": f"Failed to restart {restart_method}.",
                "stderr": stderr,
                "method": "docker" if is_docker else "systemd"
            }, status=500)
            
    except Exception as e:
        logging.error(f"Exception in restart endpoint: {str(e)}")
        return sanic.response.json({
            "status": False,
            "message": f"Exception occurred: {str(e)}"
        }, status=500)