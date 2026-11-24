# ==========================================
# ETAPA 1: Builder (Instalación de dependencias)
# ==========================================
# Se elige python:3.11-slim (Debian minimalista con glibc) frente a python:3.11-alpine
# (musl) para garantizar compatibilidad directa con ruedas binarias precompiladas
# (FastAPI, Pydantic, drivers de MongoDB/gRPC) sin compilar desde fuente,
# manteniendo al mismo tiempo una imagen ligera sin paquetes de desarrollo innecesarios.
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Crear entorno virtual aislado para transferir solo las dependencias instaladas
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar únicamente requirements.txt primero para optimizar la caché de capas de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --requirement requirements.txt

# ==========================================
# ETAPA 2: Runner (Entorno de Producción)
# ==========================================
# Imagen base minimalista sin herramientas de compilación ni caché de pip.
FROM python:3.11-slim AS runner

# Principio de mínimo privilegio: creación de grupo y usuario no root del sistema
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Copiar únicamente el entorno virtual desde la etapa builder
COPY --from=builder /opt/venv /opt/venv

# Copiar el código de la aplicación asignando propiedad al usuario no root
COPY --chown=appuser:appgroup . .

USER appuser

# Puerto HTTP de la API FastAPI
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]