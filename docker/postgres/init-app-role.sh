#!/bin/sh
set -eu

psql -v ON_ERROR_STOP=1 \
     --username "$POSTGRES_USER" \
     --dbname "$POSTGRES_DB" \
     -v app_password="$APP_DB_PASSWORD" \
     -v db_name="$POSTGRES_DB" <<'SQL'
CREATE ROLE progle_app LOGIN PASSWORD :'app_password' NOSUPERUSER NOCREATEDB NOCREATEROLE;
GRANT CONNECT ON DATABASE :"db_name" TO progle_app;
GRANT USAGE, CREATE ON SCHEMA public TO progle_app;
SQL
