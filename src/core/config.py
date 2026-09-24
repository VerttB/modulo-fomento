import os


class Settings:
    """Configurações obtidas a partir das variáveis de ambiente."""

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://fomento:fomento@localhost:5432/fomento",
    )


settings = Settings()
