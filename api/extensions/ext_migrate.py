from geo_app import geoApp


def init_app(app: geoApp):
    import flask_migrate  # type: ignore

    from extensions.ext_database import db

    flask_migrate.Migrate(app, db)
