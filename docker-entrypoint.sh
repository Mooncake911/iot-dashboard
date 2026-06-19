#!/bin/sh
set -e

: "${SPRING_INTERNAL_PORT:=8080}"
: "${GATEWAY_HOST:=iot-data-gateway}"

export SPRING_INTERNAL_PORT GATEWAY_HOST

envsubst '${SPRING_INTERNAL_PORT} ${GATEWAY_HOST}' \
  < /etc/nginx/nginx.conf.template \
  > /tmp/nginx.conf

exec nginx -c /tmp/nginx.conf -g 'daemon off;'
