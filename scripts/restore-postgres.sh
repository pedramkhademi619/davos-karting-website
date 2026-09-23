#!/usr/bin/env sh
# Restore a dump into a NEW database and print a sanity summary. It never overwrites the live database.
# Usage: scripts/restore-postgres.sh backups/davos-<stamp>.dump [target-db-name]
# To promote a restored copy, stop the application, rename databases, run `alembic upgrade head`, start again.
set -eu
DUMP="$1"
TARGET_DB="${2:-davos_restore_check}"
[ -s "$DUMP" ] || { echo "dump not found or empty: $DUMP" >&2; exit 1; }

docker compose --env-file .env.example exec -T postgres sh -c "psql -U \"\$POSTGRES_USER\" -d postgres -v ON_ERROR_STOP=1 -c 'DROP DATABASE IF EXISTS $TARGET_DB' -c 'CREATE DATABASE $TARGET_DB'"
docker compose --env-file .env.example exec -T postgres sh -c "pg_restore -U \"\$POSTGRES_USER\" -d $TARGET_DB --no-owner --exit-on-error" < "$DUMP"
docker compose --env-file .env.example exec -T postgres sh -c "psql -U \"\$POSTGRES_USER\" -d $TARGET_DB -tA -c \"select 'migration=' || version_num from alembic_version\" -c \"select 'tables=' || count(*) from information_schema.tables where table_schema='public'\""
