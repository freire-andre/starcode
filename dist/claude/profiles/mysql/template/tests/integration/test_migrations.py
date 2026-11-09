from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from {{module}}.db import get_engine

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]


def test_upgrade_write_read_downgrade() -> None:
    cfg = Config(str(ROOT / "alembic.ini"))
    engine = get_engine()
    command.upgrade(cfg, "head")
    try:
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO sample_item (name) VALUES (:name)"), {"name": "ficticio"}
            )
        with engine.connect() as conn:
            names = conn.execute(text("SELECT name FROM sample_item")).scalars().all()
        assert names == ["ficticio"]
    finally:
        command.downgrade(cfg, "base")
    assert "sample_item" not in inspect(engine).get_table_names()
    engine.dispose()
