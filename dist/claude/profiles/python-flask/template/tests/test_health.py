import pytest
from flask.testing import FlaskClient

from {{module}}.config import get_config


def test_health_returns_ok(client: FlaskClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_config_per_environment() -> None:
    assert get_config("testing").TESTING is True
    assert get_config("development").DEBUG is True
    with pytest.raises(ValueError):
        get_config("nope")
