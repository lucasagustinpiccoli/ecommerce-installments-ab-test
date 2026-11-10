#!/usr/bin/env bash
# Carga los CSV a BigQuery con schemas explicitos (sin autodetect) y crea las vistas.
# Requiere el Google Cloud SDK, `gcloud auth login` y `gcloud config set project <id>`.
# El proyecto entra en el sandbox gratuito de BigQuery.
set -euo pipefail

DATASET="${BQ_DATASET:-ecom_sim}"
LOCATION="${BQ_LOCATION:-US}"
DATA_DIR="${1:-data_raw}"

# En Git Bash para Windows, bq no encuentra Python por su cuenta: usa el incluido en el SDK.
BUNDLED_PYTHON="$(dirname "$(command -v bq)")/../platform/bundledpython/python.exe"
if [ -z "${CLOUDSDK_PYTHON:-}" ] && [ -f "$BUNDLED_PYTHON" ]; then
  export CLOUDSDK_PYTHON="$BUNDLED_PYTHON"
fi

bq show "$DATASET" >/dev/null 2>&1 || bq --location="$LOCATION" mk --dataset "$DATASET"

for table in products customers daily_traffic orders order_items contacts daily_stock; do
  bq --location="$LOCATION" load --replace --source_format=CSV --skip_leading_rows=1 \
    --schema="sql/schemas/$table.json" "$DATASET.$table" "$DATA_DIR/$table.csv"
done

bq --location="$LOCATION" load --replace --source_format=CSV --skip_leading_rows=1 \
  --schema="sql/schemas/ab_results.json" "$DATASET.ab_results" "outputs/ab_results_long.csv"

while read -r view; do
  sed "s/ecom_sim\./$DATASET./g" "$view" | bq --location="$LOCATION" query --use_legacy_sql=false --quiet
done < sql/views_order.txt

echo "Cargado en $DATASET. Reconciliacion:"
bq --location="$LOCATION" query --use_legacy_sql=false --format=pretty \
  "SELECT check_name, severity, expected, actual, passed FROM $DATASET.vw_dq_reconciliation"
