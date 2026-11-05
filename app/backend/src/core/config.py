from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Config(BaseSettings):
    """Configurações centralizadas e validadas do backend."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(min_length=1)
    territorios_csv_path: Path
    populacao_municipios_csv_path: Path
    ingestoes_path: Path

    simcc_identificador_url: str
    simcc_researchers_url: str
    via_cep_url: str
    maria_api_url: str = Field(min_length=1)
    maria_api_timeout_seconds: float = Field(gt=0)
    external_api_timeout_seconds: float = Field(gt=0)
    ingest_batch_size: int = Field(gt=0)
    ingest_checkpoint_interval: int = Field(gt=0)
    log_level: str
    cors_allowed_origins: str

    @field_validator(
        "territorios_csv_path", "populacao_municipios_csv_path", "ingestoes_path",
        mode="before",
    )
    @classmethod
    def resolve_paths_from_backend(cls, value: str | Path) -> Path:
        path = Path(value)
        return path if path.is_absolute() else BACKEND_ROOT / path


settings = Config()


class HopDispatcherConfig(BaseSettings):
    """Configuração exclusiva do disparador de containers Hop."""

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    hop_ingest_api_url: str = Field(min_length=1)
    hop_job_image: str = Field(min_length=1)
    hop_docker_socket: Path
    hop_project_path: Path
    hop_retry_delay_seconds: int = Field(gt=0)
