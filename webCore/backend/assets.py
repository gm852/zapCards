
import sanic
from webCore.auth import protected, check_token

assetsWebObj = sanic.Blueprint("assets", url_prefix="/assets")


assetsWebObj.static("/js/tailwind.js", "webCore/assets/js/tailwindcss.js", name="tailwind_js")

assetsWebObj.static("/js/notyf.min.js", "webCore/assets/js/notyf.min.js", name="notyf_js")
assetsWebObj.static("/css/notyf.min.css", "webCore/assets/css/notyf.min.css", name="notyf_css")

assetsWebObj.static("/js/index.js", "webCore/assets/js/index.js", name="index_js")
assetsWebObj.static("/css/index.css", "webCore/assets/css/index.css", name="index_css")
assetsWebObj.static("/js/aigeneration.js", "webCore/assets/js/aigeneration.js", name="aigeneration_js")
assetsWebObj.static("/js/settings.js", "webCore/assets/js/settings.js", name="settings_js")
assetsWebObj.static("/css/settings.css", "webCore/assets/css/settings.css", name="settings_css")

assetsWebObj.static("/images/zapCards.png", "webCore/assets/images/zapCards.png", name="zapCardspng")
