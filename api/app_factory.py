import logging
import time

from configs import geo_config
from geo_app import geoApp


# ----------------------------
# Application Factory Function
# ----------------------------
def create_flask_app_with_configs() -> geoApp:
    """
    create a raw flask app
    with configs loaded from .env file
    """
    geo_app = geoApp(__name__)
    geo_app.config.from_mapping(geo_config.model_dump())

    return geo_app


def create_app() -> geoApp:
    start_time = time.perf_counter()
    app = create_flask_app_with_configs()
    initialize_extensions(app)
    end_time = time.perf_counter()
    if geo_config.DEBUG:
        logging.info(f"Finished create_app ({round((end_time - start_time) * 1000, 2)} ms)")
    return app


def initialize_extensions(app: geoApp):
    from extensions import (
        ext_app_metrics,
        ext_blueprints,
        ext_celery,
        ext_code_based_extension,
        ext_commands,
        ext_compress,
        ext_database,
        ext_hosting_provider,
        ext_import_modules,
        ext_logging,
        ext_login,
        ext_mail,
        ext_migrate,
        ext_proxy_fix,
        ext_redis,
        ext_sentry,
        ext_set_secretkey,
        ext_storage,
        ext_timezone,
        ext_warnings,
    )

    extensions = [
        ext_timezone,
        ext_logging,
        ext_warnings,
        ext_import_modules,
        ext_set_secretkey,
        ext_compress,
        ext_code_based_extension,
        ext_database,
        ext_app_metrics,
        ext_migrate,
        ext_redis,
        ext_storage,
        ext_celery,
        ext_login,
        ext_mail,
        ext_hosting_provider,
        ext_sentry,
        ext_proxy_fix,
        ext_blueprints,
        ext_commands,
    ]
    for ext in extensions:
        short_name = ext.__name__.split(".")[-1]
        is_enabled = ext.is_enabled() if hasattr(ext, "is_enabled") else True
        if not is_enabled:
            if geo_config.DEBUG:
                logging.info(f"Skipped {short_name}")
            continue

        start_time = time.perf_counter()
        ext.init_app(app)
        end_time = time.perf_counter()
        if geo_config.DEBUG:
            logging.info(f"Loaded {short_name} ({round((end_time - start_time) * 1000, 2)} ms)")


def create_migrations_app():
    app = create_flask_app_with_configs()
    from extensions import ext_database, ext_migrate

    # Initialize only required extensions
    ext_database.init_app(app)
    ext_migrate.init_app(app)

    return app
