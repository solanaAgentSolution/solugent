from core.hosting_configuration import HostingConfiguration

hosting_configuration = HostingConfiguration()


from geo_app import geoApp


def init_app(app: geoApp):
    hosting_configuration.init_app(app)
