import os

from sqlalchemy import Engine, create_engine


def database_url() -> str:
    """URL do banco vinda de DATABASE_URL (o gate de integração define a do banco efêmero)."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("defina DATABASE_URL")
    return url


def get_engine(url: str | None = None) -> Engine:
    return create_engine(url or database_url(), pool_pre_ping=True)
