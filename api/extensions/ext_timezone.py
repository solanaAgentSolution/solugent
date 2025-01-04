import os
import time

from geo_app import geoApp


def init_app(app: geoApp):
    os.environ["TZ"] = "UTC"
    # windows platform not support tzset
    if hasattr(time, "tzset"):
        time.tzset()
