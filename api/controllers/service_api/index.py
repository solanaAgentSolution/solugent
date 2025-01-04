from flask_restful import Resource  # type: ignore

from configs import geo_config
from controllers.service_api import api


class IndexApi(Resource):
    def get(self):
        return {
            "welcome": "geo OpenAPI",
            "api_version": "v1",
            "server_version": geo_config.CURRENT_VERSION,
        }


api.add_resource(IndexApi, "/")
