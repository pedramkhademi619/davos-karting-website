#!/usr/bin/env sh
# Logical backup of the application database (custom format, restorable with pg_restore).
# Usage: scripts/backup-postgres.sh [output-dir]      Schedule daily from the host (cron / systemd timer).
# Retention: dumps older than BACKUP_RETENTION_DAYS (default 14) are removed. Copy dumps off-host as well.
set -eu
OUT_DIR="${1:-./backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$OUT_DIR"
TARGET="$OUT_DIR/davos-$STAMP.dump"

docker compose --env-file .env.example exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner' > "$TARGET"
[ -s "$TARGET" ] || { echo "backup is empty, aborting" >&2; rm -f "$TARGET"; exit 1; }
find "$OUT_DIR" -name 'davos-*.dump' -mtime "+$RETENTION_DAYS" -delete
echo "$TARGET"
