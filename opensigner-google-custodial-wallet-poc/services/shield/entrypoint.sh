#!/bin/sh
set -eu

if [ -n "${CLOUD_SQL_CONNECTION_NAME:-}" ]; then
  /cloud-sql-proxy --address 127.0.0.1 --port "${DB_PORT:-3306}" "${CLOUD_SQL_CONNECTION_NAME}" &
  export DB_HOST=127.0.0.1
  /busybox sleep 2
fi

exec /usr/bin/app "$@"
