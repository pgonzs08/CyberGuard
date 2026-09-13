# ==========================================
# ETAPA 1: Builder (Compilación de React)
# ==========================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar archivos de definición de paquetes
COPY package.json package-lock.json ./

# Instalar dependencias fijas
RUN npm ci

# Copiar el código fuente del frontend
COPY . .

# Compilar el proyecto estático con Vite (genera la carpeta dist/)
RUN npm run build

# ==========================================
# ETAPA 2: Servidor Nginx de Producción
# ==========================================
FROM nginx:alpine AS runner

# Copiar configuración personalizada de Nginx si se requiere (o usar la por defecto)
COPY --from=builder /app/dist /usr/share/nginx/html

# Configuración ligera para soporte de Client-Side Routing en React (Single Page Application)
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]