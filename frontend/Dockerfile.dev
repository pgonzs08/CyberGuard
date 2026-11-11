# Dockerfile.dev (Frontend)
FROM node:20-alpine

WORKDIR /app

# Copiamos primero los archivos de dependencias para aprovechar la caché
COPY package*.json ./
RUN npm install

# Copiamos el resto del código (aunque usaremos volúmenes, es útil para la primera build)
COPY . .

# Exponemos el puerto del servidor de desarrollo (ej. 5173 para Vite o 3000 para React standard)
EXPOSE 5173

# Comando para correr el servidor de desarrollo escuchando en todas las interfaces de red (--host)
# Asumiendo que usas Vite ('npm run dev'). Si usas Create React App, sería 'npm start'
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]