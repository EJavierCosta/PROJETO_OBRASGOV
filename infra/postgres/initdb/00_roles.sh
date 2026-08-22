#!/usr/bin/env bash
set -euo pipefail

psql \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --set=ingestion_password="$INGESTION_PASSWORD" \
  --set=dbt_password="$DBT_PASSWORD" \
  --set=frontend_password="$FRONTEND_PASSWORD" \
  --file=/docker-entrypoint-initdb.d/00_roles.template
