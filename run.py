import sanic, argparse, logging, uuid, os
from jinja2 import Environment, FileSystemLoader
import sanic.exceptions
import sanic.response
from sanic_limiter import Limiter, get_remote_address
import sanic_jwt

# webCore modules
from webCore import backend, auth
from webTools import database, tools, config, aiApi
import webCore 

# sqlalc models
from webCore.models import session

os.makedirs("./logs", exist_ok=True)  # log directory exists

logging.basicConfig(
    filename="./logs/log.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
console.setFormatter(formatter)

logging.getLogger().addHandler(console)

# load config
configObj = config.Config()

# get url and async mode
db_url = configObj.database_full_url
is_async = configObj.is_async

# session object
sessionObj = session.sessionObj(db_url, is_async)

# ai interface ollama / openai
if configObj.model_type == "openai": 
    modelObj = aiApi.chatGPT(config=configObj)
    logging.info("Using ChatGPT For Models")
elif configObj.model_type == "ollama": 
    modelObj = aiApi.OllamaModels(config=configObj)
    logging.info("Using Ollama For Models")
else:
    modelObj = None
    logging.error("Invalid 'model_type' defined in config.")

databaseObj = database.Database(configObj, sessionObj.async_session)
toolkitObj = tools.internalTools(configObj.prompt_presets_path)

argParseObj = argparse.ArgumentParser(
	prog='Zap Cards [ Dashboard ]',
	description='ZCD',
 )

# args
argParseObj.add_argument("--dev", action="store_true", help="start server in debug/development mode")
argParseObj.add_argument("--prod", action="store_true", help="start server in production mode")
argParseObj.add_argument("--debug", action="store_true", help="start server in debug mode")

argParseObj.add_argument("-p", "--port", help="adjust/change server port from default (16572)")
argParseObj.add_argument("-v", "--verbose", action="store_true", help="enable verbose terminal output")

argParseObj.add_argument("-ins", "--inpsect", action="store_true", help="Inpect worker proccesse(s) via sanics worker manager")


# initialization
dashboardObj = sanic.Sanic("ZC_dashboard")
parsedArgObj = argParseObj.parse_args()

if parsedArgObj.inpsect:
	dashboardObj.config.INSPECTOR = True
	print("[ DEBUG ] - in another terminal you can now user 'sanic inspect' to see workers and their status")
	
	
# limiter
limiter = Limiter(key_func=get_remote_address, app=dashboardObj, global_limits=["2 per minute"])
sanic_jwt.Initialize(dashboardObj, authenticate=webCore.auth.verification, cookie_set=True, cookie_expires=configObj.jwt_expire_time, secret=configObj.secret_session_token)
dashboardObj.config.OAS = False

@dashboardObj.before_server_start
async def setup_db(app, loop):
    if is_async:
        await sessionObj.init_db()
        logging.info("[DB] - The async database is ready")
        if configObj.reset_default_user:
            await databaseObj.addNewUser(roleType="admin")
            configObj.set("setup", "reset_default_user", False); configObj.save()
            logging.info("[RESET] - The default user was setup, meaning all other users and cards where")
    else:
        # for sqlite
        await sessionObj.init_db()
        logging.info("[DB] - The non-async database is ready")
        if configObj.reset_default_user:
            await databaseObj.addNewUser(roleType="admin")
            configObj.set("setup", "reset_default_user", False); configObj.save()
            logging.info("[RESET] - The default user was setup, meaning all other users and cards where")


    if not parsedArgObj.dev:
        await databaseObj.randomizeSecretSessionToken()


# handle invalid page requests
@dashboardObj.exception(sanic.exceptions.NotFound)
async def handle_404(request, exception):
	error_page = Environment(loader=FileSystemLoader('webCore/assets')).get_template('html/notFound.html')
	return sanic.response.html(error_page.render(), status=404)

# server configuration
@dashboardObj.on_request
async def contextFiller(request):
    
    # Initialized
    request.ctx.configObj = configObj
    request.ctx.databaseObj = databaseObj
    request.ctx.toolkitObj = toolkitObj
    request.ctx.authObj = auth
    
    request.ctx.modelObj = modelObj
    request.ctx.serverMode = "development" if parsedArgObj.dev else "production"
    request.ctx.secretServerToken = request.ctx.configObj.secret_session_token


# guest logic - not done
@dashboardObj.middleware("request")
async def assign_guest_session(request):
    if not getattr(request.ctx, "authSessionObj", None):
        session_id = request.cookies.get("guest_session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            print(f"New Guest Session id => {session_id}")
            request.ctx.new_guest_session = session_id
        request.ctx.guest_session_id = session_id

@dashboardObj.middleware("response")
async def set_guest_session_cookie(request, response):
    if hasattr(request.ctx, "new_guest_session"):
        response.add_cookie(
            key="guest_session_id",
            value=request.ctx.new_guest_session,
            max_age=60 * 60 * 24 * 7,
            path="/",
            httponly=request.ctx.configObj.use_https,
            secure=request.ctx.configObj.use_https
        )

# Blueprints
dashboardObj.blueprint(backend.routesWebObj)
dashboardObj.blueprint(backend.apiWebObj)
dashboardObj.blueprint(backend.assetsWebObj)
dashboardObj.blueprint(backend.modelsAPIWebObj)



if __name__ == "__main__":


	dashboardObj.run(
		host=("0.0.0.0" if not parsedArgObj.prod else "0.0.0.0"),
		port=(int(parsedArgObj.port) if parsedArgObj.port != None else 8080),
		dev=(True if parsedArgObj.dev else False),
		fast=(True if parsedArgObj.prod else False),
		debug=(True if parsedArgObj.debug else False),
		)


