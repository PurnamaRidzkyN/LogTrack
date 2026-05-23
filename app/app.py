from flask import Flask, session
from app.utils.datetime_helper import timesince


def create_app():

    app = Flask(__name__)

    # LOAD CONFIG
    app.config.from_object(
        "app.config.Config"
    )

    # REGISTER JINJA FILTER
    app.add_template_filter(
        timesince,
        "timesince"
    )

    # GLOBAL TEMPLATE VARIABLES
    @app.context_processor
    def inject_user():

        return {
            "role": session.get("role"),
            "user_name": session.get("name"),
            "user_id": session.get("user_id")
        }

    # REGISTER ROUTES
    from app.routes.web import register_routes
    register_routes(app)

    return app