import sanic
import sanic.response

from jinja2 import Environment, FileSystemLoader

from webCore.auth import protected, multi_protected

routesWebObj = sanic.Blueprint("routesWebObj", url_prefix="/")
env = Environment(loader=FileSystemLoader('webCore/assets'))

# /
@routesWebObj.route("/")
@multi_protected
async def homeWebObj_index(request):
    indexTemplateObj = env.get_template('html/index.html')

    indexRenderedTemplateObj = indexTemplateObj.render(
        isAuthenticated = request.ctx.authSessionObj
    )
        
    return sanic.response.html(indexRenderedTemplateObj)


# /login
@routesWebObj.route("/login")
async def homeWebObj_login(request):
    indexTemplateObj = env.get_template('html/login.html')
        
    indexRenderedTemplateObj = indexTemplateObj.render(
    
    )
        
    return sanic.response.html(indexRenderedTemplateObj)
    


# /settings
@routesWebObj.route("/settings")
@protected
async def homeWebObj_settings(request):
    indexTemplateObj = env.get_template('html/settings.html')

    if not hasattr(request.ctx, "authSessionObj") or request.ctx.authSessionObj["role"] != "admin":
        return sanic.redirect("/")

    indexRenderedTemplateObj = indexTemplateObj.render(
    
    )
        
    return sanic.response.html(indexRenderedTemplateObj)