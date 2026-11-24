"""EmbeddingService: cliente de embeddings de NVIDIA NIM (README 7.2 y 7.4).

Genera los vectores de:
  * documentos (`input_type="passage"`) durante la ingestión del UpdateWorker.
  * consultas (`input_type="query"`) durante las búsquedas semánticas.

Ambos usan el MISMO modelo (`NVIDIA_EMBEDDING_MODEL`), como exige README 7.2.

Errores (todos heredan de `EmbeddingError`; la capa gRPC decide el código):
  * `ValueError`                  texto vacío -> INVALID_ARGUMENT.
  * `EmbeddingUnavailableError`   NIM caído o saturado tras agotar los
                                  reintentos -> UNAVAILABLE.
  * `EmbeddingRequestError`       NIM rechazó la petición (clave inválida,
                                  parámetros no admitidos...); no se reintenta.
  * `EmbeddingResponseError`      respuesta incoherente, p. ej. cambio de
                                  dimensión por un cambio de modelo.

Las claves nunca se escriben en logs ni en mensajes de error.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Self

import httpx
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

if TYPE_CHECKING:  # solo para anotaciones; evita acoplar el módulo a pydantic
    from app.config import Settings

logger = logging.getLogger("qdrant_service.embeddings")

# Códigos HTTP transitorios, además de cualquier 5xx.
_RETRYABLE_STATUS = frozenset({408, 425, 429})
_MAX_RETRY_AFTER_SECONDS = 60.0
_BACKOFF = wait_random_exponential(multiplier=1, max=30)
_PROBE_TEXT = "dimension probe"


# ----------------------------------------------------------------------
# Excepciones
# ----------------------------------------------------------------------
class EmbeddingError(Exception):
    """Error base del servicio de embeddings."""


class EmbeddingUnavailableError(EmbeddingError):
    """NVIDIA NIM no está disponible (reintentos agotados)."""


class EmbeddingRequestError(EmbeddingError):
    """NVIDIA NIM rechazó la petición; reintentar no ayudaría."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class EmbeddingResponseError(EmbeddingError):
    """La respuesta de NVIDIA NIM es inválida o incoherente."""


class _RetryableStatusError(Exception):
    """Respuesta HTTP transitoria (429, 5xx...). Uso interno."""

    def __init__(self, status_code: int, retry_after: float | None = None) -> None:
        super().__init__(f"HTTP {status_code}")
        self.status_code = status_code
        self.retry_after = retry_after


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------
def _is_retryable_status(status: int) -> bool:
    return status in _RETRYABLE_STATUS or status >= 500


def _parse_retry_after(value: str | None) -> float | None:
    """Interpreta `Retry-After` en segundos. El formato de fecha HTTP se ignora."""
    if not value:
        return None
    try:
        seconds = float(value)
    except ValueError:
        return None
    return seconds if seconds >= 0 else None


def _wait_strategy(retry_state: RetryCallState) -> float:
    """Backoff exponencial con jitter, respetando `Retry-After` si es mayor."""
    delay = _BACKOFF(retry_state)
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    if isinstance(exc, _RetryableStatusError) and exc.retry_after is not None:
        delay = max(delay, min(exc.retry_after, _MAX_RETRY_AFTER_SECONDS))
    return delay


def _describe(exc: BaseException | None) -> str:
    if exc is None:
        return "error desconocido"
    if isinstance(exc, _RetryableStatusError):
        return f"HTTP {exc.status_code}"
    return f"{type(exc).__name__}: {exc}"


def _log_before_sleep(retry_state: RetryCallState) -> None:
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    sleep = retry_state.next_action.sleep if retry_state.next_action else 0.0
    logger.warning(
        "Fallo transitorio con NVIDIA NIM (intento %d): %s. Reintentando en %.1f s",
        retry_state.attempt_number,
        _describe(exc),
        sleep,
    )


def _clean_text(text: Any, what: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"El texto de {what} no puede estar vacío")
    return text.strip()


def _parse_embeddings(body: Any, expected: int) -> list[list[float]]:
    """Valida la respuesta y devuelve los vectores en el orden de la entrada."""
    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, list) or len(data) != expected:
        raise EmbeddingResponseError(
            f"Respuesta inválida de NVIDIA NIM: se esperaban {expected} embeddings"
        )
    if not all(isinstance(item, dict) for item in data):
        raise EmbeddingResponseError("Respuesta inválida de NVIDIA NIM: formato inesperado")

    # El orden por `index` es el contrato de la API; se respeta aunque lleguen desordenados.
    ordered = sorted(data, key=lambda item: item.get("index", 0))
    vectors: list[list[float]] = []
    for item in ordered:
        vector = item.get("embedding")
        if (
            not isinstance(vector, list)
            or not vector
            or not all(isinstance(x, (int, float)) for x in vector)
        ):
            raise EmbeddingResponseError("Respuesta inválida de NVIDIA NIM: embedding no numérico")
        vectors.append([float(x) for x in vector])
    return vectors


# ----------------------------------------------------------------------
# Servicio
# ----------------------------------------------------------------------
class EmbeddingService:
    """Cliente asíncrono de la API de embeddings de NVIDIA NIM."""

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._model = settings.nvidia_embedding_model
        self._url = settings.nvidia_embeddings_url
        self._use_input_type = settings.nvidia_use_input_type
        self._truncate = settings.nvidia_truncate
        self._batch_size = settings.embedding_batch_size
        self._max_retries = settings.nvidia_max_retries

        self._semaphore = asyncio.Semaphore(settings.nvidia_max_concurrency)
        self._owns_client = client is None
        self._client = client if client is not None else self._build_client(settings)

        self._dimension: int | None = None
        self._health: tuple[float, bool] | None = None
        self._health_lock = asyncio.Lock()

    @staticmethod
    def _build_client(settings: Settings) -> httpx.AsyncClient:
        timeout = settings.nvidia_timeout_seconds
        concurrency = settings.nvidia_max_concurrency
        return httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {settings.nvidia_api_key.get_secret_value()}",
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(timeout, connect=min(10.0, timeout)),
            limits=httpx.Limits(
                max_connections=concurrency,
                max_keepalive_connections=concurrency,
            ),
        )

    async def aclose(self) -> None:
        """Libera el cliente HTTP (solo si lo creó este servicio)."""
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    async def embed_query(self, text: str) -> list[float]:
        """Vector de una consulta (`input_type="query"`)."""
        cleaned = _clean_text(text, "la consulta")
        vectors = await self._embed([cleaned], "query")
        return vectors[0]

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Vectores de documentos (`input_type="passage"`), en el orden recibido.

        Divide la entrada en lotes de `EMBEDDING_BATCH_SIZE`. Los lotes se envían
        de uno en uno, de modo que la ingestión nunca acapara toda la concurrencia
        y las consultas de los usuarios siguen atendiéndose.
        """
        if not texts:
            return []
        cleaned = [_clean_text(t, f"el documento {i}") for i, t in enumerate(texts)]

        vectors: list[list[float]] = []
        for start in range(0, len(cleaned), self._batch_size):
            batch = cleaned[start : start + self._batch_size]
            vectors.extend(await self._embed(batch, "passage"))
        return vectors

    async def get_dimension(self) -> int:
        """Dimensión de los vectores del modelo configurado.

        Se detecta con una petición mínima la primera vez y se guarda. Así no
        puede desajustarse de `NVIDIA_EMBEDDING_MODEL`. QdrantHandler la usa para
        crear las colecciones y para detectar si cambió el modelo (README 7.5).
        """
        if self._dimension is None:
            await self.embed_query(_PROBE_TEXT)
        assert self._dimension is not None
        return self._dimension

    async def check_health(self, max_age_seconds: float = 30.0) -> bool:
        """¿Responde NVIDIA NIM? Alimenta el estado DEGRADED de HealthCheck.

        Hace una única petición, sin reintentos, y guarda el resultado
        `max_age_seconds` para que la monitorización no consuma cuota.
        """
        async with self._health_lock:
            now = time.monotonic()
            if self._health is not None and now - self._health[0] < max_age_seconds:
                return self._health[1]
            try:
                body = await self._post_once(self._build_payload([_PROBE_TEXT], "query"))
                _parse_embeddings(body, 1)
                ok = True
            except Exception as exc:  # noqa: BLE001 - cualquier fallo significa "no disponible"
                logger.warning("NVIDIA NIM no responde correctamente: %s", _describe(exc))
                ok = False
            self._health = (time.monotonic(), ok)
            return ok

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------
    def _build_payload(self, texts: list[str], input_type: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self._model,
            "input": texts,
            "encoding_format": "float",
        }
        if self._use_input_type:
            payload["input_type"] = input_type
        if self._truncate:
            payload["truncate"] = self._truncate
        return payload

    async def _embed(self, texts: list[str], input_type: str) -> list[list[float]]:
        body = await self._post_with_retries(self._build_payload(texts, input_type))
        vectors = _parse_embeddings(body, len(texts))
        self._check_dimension(vectors)
        return vectors

    def _check_dimension(self, vectors: list[list[float]]) -> None:
        dimensions = {len(v) for v in vectors}
        if len(dimensions) != 1:
            raise EmbeddingResponseError("NVIDIA NIM devolvió vectores de distinta dimensión")
        dimension = dimensions.pop()
        if self._dimension is None:
            self._dimension = dimension
            logger.info(
                "Dimensión de embeddings detectada: %d (modelo %s)", dimension, self._model
            )
        elif dimension != self._dimension:
            raise EmbeddingResponseError(
                f"NVIDIA NIM devolvió vectores de dimensión {dimension} y se esperaba "
                f"{self._dimension}: ¿ha cambiado NVIDIA_EMBEDDING_MODEL?"
            )

    async def _post_once(self, payload: dict[str, Any]) -> Any:
        """Una petición, sin reintentos. Clasifica los fallos."""
        async with self._semaphore:  # solo durante la petición, no durante el backoff
            response = await self._client.post(self._url, json=payload)

        if response.is_success:
            try:
                return response.json()
            except ValueError as exc:
                raise EmbeddingResponseError(
                    "NVIDIA NIM devolvió una respuesta que no es JSON"
                ) from exc

        status = response.status_code
        if _is_retryable_status(status):
            raise _RetryableStatusError(
                status, _parse_retry_after(response.headers.get("Retry-After"))
            )
        raise EmbeddingRequestError(
            f"NVIDIA NIM rechazó la petición (HTTP {status}): {response.text[:300]}",
            status_code=status,
        )

    async def _post_with_retries(self, payload: dict[str, Any]) -> Any:
        attempts = self._max_retries + 1
        retrying = AsyncRetrying(
            stop=stop_after_attempt(attempts),
            wait=_wait_strategy,
            retry=retry_if_exception_type((httpx.TransportError, _RetryableStatusError)),
            before_sleep=_log_before_sleep,
            reraise=True,
        )
        body: Any = None
        try:
            async for attempt in retrying:
                with attempt:
                    body = await self._post_once(payload)
        except (httpx.TransportError, _RetryableStatusError) as exc:
            raise EmbeddingUnavailableError(
                f"NVIDIA NIM no disponible tras {attempts} intentos ({_describe(exc)})"
            ) from exc
        return body