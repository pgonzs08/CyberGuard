"""Configuración centralizada de qdrant_service.

Todos los valores proceden de variables de entorno (las inyecta Docker Compose)
y se validan al arrancar: si falta algo imprescindible o hay un valor inválido,
el servicio falla de inmediato con un mensaje claro en lugar de hacerlo más
tarde, en mitad de una ingestión o de una consulta.

Uso:

    from app.config import get_settings

    settings = get_settings()
    settings.qdrant_url

Variables de entorno (el nombre es el del campo en mayúsculas):

    Obligatorias
        NVIDIA_API_KEY              Clave de NVIDIA NIM.
        NVIDIA_EMBEDDING_MODEL      Modelo de embeddings. Debe ser el mismo en la
                                    ingestión y en las consultas (README 7.2).

    Opcionales: ver los valores por defecto en la clase `Settings`.
"""

from functools import lru_cache
from typing import Literal

from pydantic import (
    Field,
    SecretStr,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigError(RuntimeError):
    """La configuración del servicio es inválida o está incompleta."""


class Settings(BaseSettings):
    """Ajustes de qdrant_service, leídos del entorno y validados."""

    model_config = SettingsConfigDict(
        case_sensitive=False,  # QDRANT_HOST -> qdrant_host
        extra="ignore",  # el entorno contiene muchas variables ajenas
        frozen=True,  # los ajustes no cambian una vez cargados
    )

    # ------------------------------------------------------------------
    # Servicio HTTP (healthcheck y documentación)
    # ------------------------------------------------------------------
    service_host: str = "0.0.0.0"
    service_port: int = Field(8080, ge=1, le=65535)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    uvicorn_reload: bool = False

    # ------------------------------------------------------------------
    # Servidor gRPC (interfaz de solo lectura para el backend)
    # ------------------------------------------------------------------
    grpc_host: str = "0.0.0.0"
    grpc_port: int = Field(50051, ge=1, le=65535)

    # ------------------------------------------------------------------
    # Qdrant (base de datos vectorial)
    # ------------------------------------------------------------------
    qdrant_host: str = "localhost"
    qdrant_port: int = Field(6333, ge=1, le=65535)
    qdrant_cve_collection: str = Field("cyberguard_cves", min_length=1)
    qdrant_mitre_collection: str = Field("cyberguard_mitre_attack", min_length=1)

    # ------------------------------------------------------------------
    # NVIDIA NIM (embeddings)
    # ------------------------------------------------------------------
    nvidia_api_key: SecretStr
    nvidia_embedding_model: str
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_timeout_seconds: float = Field(30.0, gt=0)
    nvidia_max_retries: int = Field(5, ge=0)
    embedding_batch_size: int = Field(32, ge=1)
    nvidia_max_concurrency: int = Field(4, ge=1)
    nvidia_use_input_type: bool = True
    nvidia_truncate: Literal["NONE", "START", "END"] | None = "END"
 

    # ------------------------------------------------------------------
    # Sincronización autónoma (UpdateWorker, README 7.5)
    # ------------------------------------------------------------------
    sync_enabled: bool = True
    sync_interval_hours: float = Field(24.0, gt=0)
    nvd_api_url: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    # Opcional, pero el NVD limita mucho las peticiones sin clave.
    nvd_api_key: SecretStr | None = None
    mitre_attack_url: str = (
        "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/"
        "master/enterprise-attack/enterprise-attack.json"
    )

    # ------------------------------------------------------------------
    # Límites de las consultas gRPC (ver comentarios de qdrant_service.proto)
    # ------------------------------------------------------------------
    search_default_limit: int = Field(5, ge=1)
    search_max_limit: int = Field(20, ge=1)
    list_default_page_size: int = Field(20, ge=1)
    list_max_page_size: int = Field(100, ge=1)

    # ------------------------------------------------------------------
    # Validadores
    # ------------------------------------------------------------------
    @field_validator("log_level", mode="before")
    @classmethod
    def _normalizar_log_level(cls, v):
        return v.strip().upper() if isinstance(v, str) else v

    @field_validator("nvidia_api_key", mode="before")
    @classmethod
    def _clave_nvidia_no_vacia(cls, v):
        # Compose entrega una cadena vacía si la variable no está definida en .env
        raw = v.get_secret_value() if isinstance(v, SecretStr) else v
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("no puede estar vacía; defínela en el archivo .env")
        return raw.strip()

    @field_validator("nvidia_embedding_model", mode="before")
    @classmethod
    def _modelo_no_vacio(cls, v):
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError("no puede estar vacío; defínelo en el archivo .env")
        return v

    @field_validator("nvd_api_key", mode="before")
    @classmethod
    def _clave_nvd_opcional(cls, v):
        # Una cadena vacía equivale a "sin clave".
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("nvidia_base_url", "nvd_api_url", "mitre_attack_url")
    @classmethod
    def _validar_url(cls, v: str) -> str:
        v = v.strip().rstrip("/")
        if not v.startswith(("http://", "https://")):
            raise ValueError("debe empezar por http:// o https://")
        return v

    @model_validator(mode="after")
    def _validar_coherencia(self) -> "Settings":
        if self.qdrant_cve_collection == self.qdrant_mitre_collection:
            raise ValueError(
                "QDRANT_CVE_COLLECTION y QDRANT_MITRE_COLLECTION deben ser "
                "colecciones distintas"
            )
        if self.search_default_limit > self.search_max_limit:
            raise ValueError(
                "SEARCH_DEFAULT_LIMIT no puede superar SEARCH_MAX_LIMIT"
            )
        if self.list_default_page_size > self.list_max_page_size:
            raise ValueError(
                "LIST_DEFAULT_PAGE_SIZE no puede superar LIST_MAX_PAGE_SIZE"
            )
        return self

    # ------------------------------------------------------------------
    # Valores derivados
    # ------------------------------------------------------------------
    @property
    def qdrant_url(self) -> str:
        return f"http://{self.qdrant_host}:{self.qdrant_port}"

    @property
    def nvidia_embeddings_url(self) -> str:
        return f"{self.nvidia_base_url}/embeddings"

    @property
    def sync_interval_seconds(self) -> float:
        return self.sync_interval_hours * 3600


    def resolve_limit(self, requested: int) -> int:
        if requested <= 0:
            return self.search_default_limit
        return min(requested, self.search_max_limit)

    def resolve_page_size(self, requested: int) -> int:
        if requested <= 0:
            return self.list_default_page_size
        return min(requested, self.list_max_page_size)


def _formatear_errores(exc: ValidationError) -> str:
    """Resume los errores usando el nombre de la variable de entorno.

    No incluye los valores recibidos, para no volcar claves en los logs.
    """
    partes = []
    for err in exc.errors(include_url=False, include_input=False):
        variable = ".".join(str(p) for p in err["loc"]).upper() or "CONFIGURACIÓN"
        partes.append(f"{variable}: {err['msg']}")
    return "; ".join(partes)


@lru_cache
def get_settings() -> Settings:
    """Devuelve los ajustes (se cargan y validan una sola vez).

    En pruebas, `get_settings.cache_clear()` fuerza una nueva lectura del entorno.
    """
    try:
        return Settings()
    except ValidationError as exc:
        raise ConfigError(
            f"Configuración inválida de qdrant_service -> {_formatear_errores(exc)}"
        ) from None
