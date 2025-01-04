from geo_app import geoApp


def init_app(app: geoApp):
    import warnings

    warnings.simplefilter("ignore", ResourceWarning)
