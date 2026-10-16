#!/bin/sh
set -e

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Aplicando migrations (alembic upgrade head)..."
  alembic upgrade head
fi

exec "$@"
