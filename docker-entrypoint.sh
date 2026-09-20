#!/bin/sh
set -e

: "${SPRING_INTERNAL_PORT:=8080}"
: "${GATEWAY_HOST:=iot-data-gateway}"
: "${GRAFANA_HOST:=grafana}"
: "${PROMETHEUS_HOST:=prometheus}"

export SPRING_INTERNAL_PORT GATEWAY_HOST GRAFANA_HOST PROMETHEUS_HOST

envsubst '${SPRING_INTERNAL_PORT} ${GATEWAY_HOST} ${GRAFANA_HOST} ${PROMETHEUS_HOST}' \
  < /etc/nginx/nginx.conf.template \
  > /tmp/nginx.conf

exec nginx -c /tmp/nginx.conf -g 'daemon off;'
