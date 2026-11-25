# ==========================================
# ETAPA 1: Builder (Instalación de dependencias)
# ==========================================
# Se elige python:3.11-slim frente a alpine porque las librerías cliente de Qdrant,
# gRPC (grpcio) y utilidades de procesamiento numérico disponen de ruedas manylinux
# (glibc) optimizadas; usar slim evita compilar C/C++ en build y mantiene un tamaño reducido.
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Crear entorno virtual aislado para aislar las dependencias de compilación
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar requirements.txt antes del código fuente para aprovechar la caché de capas
COPY requirements.txt .
RUN pip install --no-cache-dir --requirement requirements.txt

# ==========================================
# ETAPA 2: Runner (Entorno de Producción)
# ==========================================
# Imagen base minimalista para ejecución aislada de la API REST y el servidor gRPC.
FROM python:3.11-slim AS runner

# Principio de mínimo privilegio: creación de grupo y usuario no root del sistema
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Copiar únicamente el entorno virtual compilado en la etapa builder
COPY --from=builder /opt/venv /opt/venv

# Copiar el código del microservicio con propiedad del usuario no root
COPY --chown=appuser:appgroup . .

USER appuser

# Puerto 8080: API HTTP (healthcheck y sincronización)
# Puerto 50051: Servidor gRPC de solo lectura para consultas internas desde el backend
EXPOSE 8080 50051

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
