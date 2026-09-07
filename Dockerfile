# ---- Stage 1: Build ----
FROM node:22-alpine AS builder
WORKDIR /app

# Копируем package-файлы и устанавливаем зависимости (включая dev — нужны для сборки)
COPY package*.json ./
RUN npm ci && npm cache clean --force

# Копируем исходники и собираем статику
COPY . .
ARG VITE_GATEWAY_URL=
ENV VITE_GATEWAY_URL=$VITE_GATEWAY_URL
RUN npm run build

# ---- Stage 2: Production ----
FROM nginx:alpine AS dashboard-ui

RUN apk add --no-cache gettext \
    && mkdir -p /tmp/nginx/client_body /tmp/nginx/proxy /tmp/nginx/fastcgi /tmp/nginx/uwsgi /tmp/nginx/scgi \
    && chown -R nginx:nginx /tmp/nginx /usr/share/nginx/html /var/cache/nginx /var/log/nginx

COPY nginx.conf.template /etc/nginx/nginx.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

ARG SPRING_INTERNAL_PORT=8080
EXPOSE ${SPRING_INTERNAL_PORT}

ENTRYPOINT ["/docker-entrypoint.sh"]
