from core.extension.extension import Extension
from geo_app import geoApp


def init_app(app: geoApp):
    code_based_extension.init()


code_based_extension = Extension()
