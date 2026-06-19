# ---- Stage 1: Build ----
FROM node:22-alpine AS builder
WORKDIR /app

# Копируем package-файлы и устанавливаем зависимости (включая dev — нужны для сборки)
COPY package*.json ./
RUN npm ci && npm cache clean --force

# Копируем исходники и собираем статику
COPY . .
ARG VITE_GATEWAY_URL=http://localhost:8085
ENV VITE_GATEWAY_URL=$VITE_GATEWAY_URL
RUN npm run build

# ---- Stage 2: Production ----
FROM nginx:alpine AS dashboard-ui

# Директории для nginx под непривилегированным пользователем
RUN mkdir -p /tmp/nginx/client_body /tmp/nginx/proxy /tmp/nginx/fastcgi /tmp/nginx/uwsgi /tmp/nginx/scgi \
    && chown -R nginx:nginx /tmp/nginx /usr/share/nginx/html /var/cache/nginx /var/log/nginx

COPY nginx.conf /etc/nginx/nginx.conf

# Копируем собранную статику в папку nginx
COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

USER nginx

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]