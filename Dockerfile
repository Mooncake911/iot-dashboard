# ---- Stage 1: Build ----
FROM node:22-alpine AS builder
WORKDIR /app

# Копируем package-файлы и устанавливаем зависимости
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Копируем исходники и собираем статику
COPY . .
ARG VITE_GATEWAY_URL=http://localhost:8085
ENV VITE_GATEWAY_URL=$VITE_GATEWAY_URL
RUN npm run build

# ---- Stage 2: Production ----
FROM nginx:alpine AS dashboard-ui

# Создаём непривилегированного пользователя
RUN addgroup -g 1001 -S nginx && adduser -S nginx -u 1001

# Копируем собранную статику в папку nginx
COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

# (Опционально) кастомный nginx.conf для SPA (если нужно)
# COPY nginx.conf /etc/nginx/nginx.conf

# Переключаемся на непривилегированного пользователя
USER nginx

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]