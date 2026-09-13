# ==========================================
# ETAPA 1: Builder (Instalación de dependencias)
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Evitar que Python escriba archivos .pyc y forzar salida sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema necesarias para compilar ciertas librerías C/C++
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependencias de Python en un entorno de usuario
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ==========================================
# ETAPA 2: Runner de Producción
# ==========================================
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Copiar el entorno virtual completo ya compilado desde la etapa builder
COPY --from=builder /opt/venv /opt/venv

# Asegurar que el sistema use el binario del entorno virtual por defecto
ENV PATH="/opt/venv/bin:$PATH"

# Copiar el código fuente de la aplicación
COPY . .

# Crear un usuario no raíz por seguridad (Buenas prácticas de contenedorización)
RUN useradd -m appuser && chown -R appuser:appuser .
USER appuser

# Exponer el puerto de FastAPI
EXPOSE 8000

# Comando de arranque usando Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]