from collections.abc import Mapping
from typing import Any

from flask import Flask

from .config import get_config
from .health import bp as health_bp


def create_app(env: str | None = None, overrides: Mapping[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(env))
    if overrides:
        app.config.from_mapping(overrides)
    app.register_blueprint(health_bp)
    return app
