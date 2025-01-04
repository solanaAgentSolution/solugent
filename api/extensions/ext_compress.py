from configs import geo_config
from geo_app import geoApp


def is_enabled() -> bool:
    return geo_config.API_COMPRESSION_ENABLED


def init_app(app: geoApp):
    from flask_compress import Compress  # type: ignore

    compress = Compress()
    compress.init_app(app)
