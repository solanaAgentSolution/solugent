from geo_app import geoApp
from models import db


def init_app(app: geoApp):
    db.init_app(app)
