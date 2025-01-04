from geo_app import geoApp


def init_app(app: geoApp):
    from events import event_handlers  # noqa: F401
