from configs import geo_config
from geo_app import geoApp


def init_app(app: geoApp):
    if geo_config.RESPECT_XFORWARD_HEADERS_ENABLED:
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app)  # type: ignore
