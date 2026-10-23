#!/bin/sh
# The karting game keeps its leaderboard in its own database (davos_game) with its own login (game), apart from the
# booking data: the game cannot read or change anything else. Safe to run again (it only creates what is missing), which
# is how an installation whose data volume already exists gets it:
#   docker compose exec -T postgres sh /docker-entrypoint-initdb.d/20-game-db.sh
# On a brand-new volume the postgres image runs it by itself, once, at first start.
set -e
: "${GAME_DB_PASSWORD:?GAME_DB_PASSWORD is not set}"
psql -v ON_ERROR_STOP=1 -v game_password="$GAME_DB_PASSWORD" --username "$POSTGRES_USER" --dbname postgres <<'SQL'
SELECT format('CREATE ROLE game LOGIN PASSWORD %L', :'game_password')
 WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'game') \gexec
SELECT format('ALTER ROLE game PASSWORD %L', :'game_password') \gexec
SELECT 'CREATE DATABASE davos_game OWNER game'
 WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'davos_game') \gexec
SQL
