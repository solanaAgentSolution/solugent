from configs import geo_config
from geo_app import geoApp


def init_app(app: geoApp):
    if geo_config.SENTRY_DSN:
        import openai
        import sentry_sdk
        from langfuse import parse_error  # type: ignore
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.flask import FlaskIntegration
        from werkzeug.exceptions import HTTPException

        from core.model_runtime.errors.invoke import InvokeRateLimitError

        def before_send(event, hint):
            if "exc_info" in hint:
                exc_type, exc_value, tb = hint["exc_info"]
                if parse_error.defaultErrorResponse in str(exc_value):
                    return None

            return event

        sentry_sdk.init(
            dsn=geo_config.SENTRY_DSN,
            integrations=[FlaskIntegration(), CeleryIntegration()],
            ignore_errors=[
                HTTPException,
                ValueError,
                FileNotFoundError,
                openai.APIStatusError,
                InvokeRateLimitError,
                parse_error.defaultErrorResponse,
            ],
            traces_sample_rate=geo_config.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=geo_config.SENTRY_PROFILES_SAMPLE_RATE,
            environment=geo_config.DEPLOY_ENV,
            release=f"geo-{geo_config.CURRENT_VERSION}-{geo_config.COMMIT_SHA}",
            before_send=before_send,
        )
