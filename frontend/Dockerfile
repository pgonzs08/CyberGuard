# ==========================================
# ETAPA 1: Builder (Compilación de React/Vite)
# ==========================================
# Se utiliza node:22.14.0-alpine (imagen mínima basada en Alpine Linux) para
# mantener un tamaño reducido frente a variantes Debian y aislar el entorno
# de compilación del de ejecución.
FROM node:22.14.0-alpine AS builder

WORKDIR /app

# Copiar manifiestos de dependencias primero para optimizar la caché de capas
COPY package.json package-lock.json ./
RUN npm ci

# Copiar el código fuente y generar el bundle estático en /app/dist
COPY . .
RUN npm run build

# ==========================================
# ETAPA 2: Servidor Estático Minimalista (Caddy)
# ==========================================
# Se utiliza caddy:2.10.2-alpine como imagen base mínima para servir
# archivos estáticos con soporte SPA (fallback a index.html) sin arrastrar
# herramientas de compilación ni el runtime de Node.js.
# Ajusta la etiqueta fijada a la versión exacta deseada de Caddy.
FROM caddy:2.10.2-alpine AS runner

# Crear grupo y usuario no root (principio de mínimo privilegio)
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /srv

# Copiar únicamente los archivos estáticos compilados con permisos del usuario no root
COPY --from=builder --chown=appuser:appgroup /app/dist /srv

# Configurar Caddy en puerto no privilegiado 8080 con soporte SPA y almacenamiento en /tmp
RUN mkdir -p /etc/caddy /tmp/caddy-data /tmp/caddy-config && \
    printf ':8080 {\n\
    root * /srv\n\
    try_files {path} /index.html\n\
    file_server\n\
    encode gzip\n\
}\n' > /etc/caddy/Caddyfile && \
    chown -R appuser:appgroup /srv /etc/caddy /tmp/caddy-data /tmp/caddy-config

ENV XDG_DATA_HOME=/tmp/caddy-data \
    XDG_CONFIG_HOME=/tmp/caddy-config

USER appuser

EXPOSE 8080

CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]