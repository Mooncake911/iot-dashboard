# Stage 1: Build
FROM node:22-alpine AS builder
WORKDIR /app

# Копируем package-файлы и устанавливаем зависимости
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Копируем исходники и собираем статику
COPY . .
RUN npm run build

# Stage 2: Production
FROM nginx:alpine AS dashboard-ui

# Создаём непривилегированного пользователя (nginx уже существует, но для надёжности)
RUN addgroup -g 1001 -S nginx && adduser -S nginx -u 1001

# Копируем собранные файлы в nginx
COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

# Копируем кастомный конфиг nginx (опционально)
# COPY nginx.conf

# Переключаемся на непривилегированного пользователя
USER nginx

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]