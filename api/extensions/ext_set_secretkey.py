from configs import geo_config
from geo_app import geoApp


def init_app(app: geoApp):
    app.secret_key = geo_config.SECRET_KEY
