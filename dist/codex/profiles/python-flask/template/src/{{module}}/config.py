import os


class Config:
    TESTING = False
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    pass


_CONFIGS: dict[str, type[Config]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(env: str | None = None) -> type[Config]:
    """Escolhe a configuração pelo argumento ou por APP_ENV (padrão: production)."""
    name = env or os.environ.get("APP_ENV", "production")
    try:
        return _CONFIGS[name]
    except KeyError:
        raise ValueError(f"ambiente desconhecido: {name}") from None
