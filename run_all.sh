#!/usr/bin/env bash
# Regenera todo el proyecto desde cero. Si `bq` no esta instalado, verifica localmente
# con DuckDB y saltea solo la carga a BigQuery.
set -euo pipefail
cd "$(dirname "$0")"

python scripts/generate_data.py data_raw
python scripts/ab_test.py data_raw outputs
python scripts/verify_local.py data_raw outputs

if command -v bq >/dev/null 2>&1; then
  bash scripts/load_bigquery.sh data_raw
else
  echo "bq no esta instalado: se saltea la carga a BigQuery (ver docs/README.md)."
fi
