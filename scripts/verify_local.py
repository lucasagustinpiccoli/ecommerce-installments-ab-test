"""
Prueba las vistas SQL sin BigQuery: las traduce a DuckDB, las ejecuta sobre los CSV y
compara contra ab_test.py y los valores de control del brief.
No reemplaza una corrida real en BigQuery: valida logica y resultados, no el dialecto.

Salida: outputs/data_quality_results.csv, outputs/view_control_results.csv
Falla (exit 1) ante un chequeo bloqueante o un valor de control que no coincide.

Uso:  python scripts/verify_local.py [carpeta_datos] [carpeta_salida]
"""
import glob
import json
import os
import re
import sys

import duckdb
import pandas as pd
import sqlglot

DATA = sys.argv[1] if len(sys.argv) > 1 else "data_raw"
OUT = sys.argv[2] if len(sys.argv) > 2 else "outputs"
TYPES = {"INT64": "BIGINT", "FLOAT64": "DOUBLE", "STRING": "VARCHAR", "DATE": "DATE", "DATETIME": "TIMESTAMP"}

con = duckdb.connect()
con.execute("CREATE SCHEMA ecom_sim")

for path in sorted(glob.glob("sql/schemas/*.json")):
    table = os.path.basename(path)[:-5]
    csv = os.path.join(DATA, f"{table}.csv") if table != "ab_results" else os.path.join(OUT, "ab_results_long.csv")
    with open(path, encoding="utf-8") as f:
        schema = json.load(f)
    cols = ", ".join(f"'{c['name']}': '{TYPES[c['type']]}'" for c in schema)
    con.execute(f"CREATE TABLE ecom_sim.{table} AS SELECT * FROM read_csv('{csv}', header=true, columns={{{cols}}})")
    for c in schema:
        if c["mode"] == "REQUIRED":
            n = con.execute(f"SELECT COUNT(*) FROM ecom_sim.{table} WHERE {c['name']} IS NULL").fetchone()[0]
            if n:
                sys.exit(f"{table}.{c['name']} es REQUIRED y tiene {n} nulos")

# Las vistas dependen entre si: sql/views_order.txt fija el orden y debe incluirlas todas.
with open("sql/views_order.txt", encoding="utf-8") as f:
    views = f.read().split()
missing = {p.replace(os.sep, "/") for p in glob.glob("sql/[0-9]*/*.sql")} - set(views)
if missing:
    sys.exit(f"Faltan en sql/views_order.txt: {sorted(missing)}")
for path in views:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if not re.match(r"\s*-- Pregunta:", text):
        sys.exit(f"{path}: falta el comentario de definicion")
    con.execute(sqlglot.transpile(text, read="bigquery", write="duckdb")[0])
print(f"Vistas creadas y ejecutadas: {len(views)}")

for path in views:
    name = os.path.basename(path)[:-4]
    n = con.execute(f"SELECT COUNT(*) FROM ecom_sim.{name}").fetchone()[0]
    if n == 0:
        sys.exit(f"{name} no devolvio filas")

# ---------------------------------------------------------- calidad de datos
dq = con.execute("SELECT * FROM ecom_sim.vw_dq_reconciliation").df()
dq.to_csv(os.path.join(OUT, "data_quality_results.csv"), index=False)
print(dq.to_string(index=False))
blocking = dq[(dq.severity == "blocking") & (~dq.passed)]

# ---------------------------------------------------------- control de vistas
with open(os.path.join(OUT, "ab_results.json"), encoding="utf-8") as f:
    ab = json.load(f)
one = lambda q: con.execute(q).fetchone()[0]
ab_row = lambda v, col: one(f"SELECT {col} FROM ecom_sim.vw_ab_summary WHERE checkout_variant = '{v}'")
ops = lambda col, where: one(f"SELECT AVG({col}) FROM ecom_sim.vw_ops_by_stage WHERE {where}")
prof = lambda col, where: one(f"SELECT AVG({col}) FROM ecom_sim.vw_profitability_by_stage WHERE {where}")
EVENT = "stage IN ('2_cyber_monday', '4_black_friday')"
NORMAL = "stage NOT IN ('2_cyber_monday', '4_black_friday')"
c_ab = ab["contribution_after_ads_per_1000_sessions"]
c_ref = ab["contribution_after_ads_returns_refunded"]

CONTROL = [  # nombre, valor de la vista, esperado, tolerancia
    ("A/B conversion A = python", ab_row("A", "conversion"), ab["conversion"]["a"], 1e-9),
    ("A/B conversion B = python", ab_row("B", "conversion"), ab["conversion"]["b"], 1e-9),
    ("A/B ticket A = python", ab_row("A", "ticket"), ab["ticket"]["a"], 1e-4),
    ("A/B ticket B = python", ab_row("B", "ticket"), ab["ticket"]["b"], 1e-4),
    ("A/B contrib A = python", ab_row("A", "contribution_after_ads_per_1000_sessions"), c_ab["a_per_1000"], 1e-4),
    ("A/B contrib B = python", ab_row("B", "contribution_after_ads_per_1000_sessions"), c_ab["b_per_1000"], 1e-4),
    ("A/B reembolso A = python", ab_row("A", "contribution_refunded_after_ads_per_1000_sessions"), c_ref["a_per_1000"], 1e-4),
    ("A/B reembolso B = python", ab_row("B", "contribution_refunded_after_ads_per_1000_sessions"), c_ref["b_per_1000"], 1e-4),
    ("Conversion global %", one("SELECT SUM(orders_funnel) / SUM(sessions) * 100 FROM ecom_sim.vw_funnel_daily"), 3.46, 0.005),
    ("Recompra %", one("SELECT repurchase_rate * 100 FROM ecom_sim.vw_repurchase_rate"), 18.1, 0.05),
    ("ROAS busqueda", one("SELECT roas_booked FROM ecom_sim.vw_acquisition_by_channel WHERE channel = 'paid_search'"), 3.6, 0.05),
    ("ROAS social", one("SELECT roas_booked FROM ecom_sim.vw_acquisition_by_channel WHERE channel = 'social_ads'"), 2.4, 0.05),
    ("Margen bruto normal %", prof("gross_margin", NORMAL) * 100, 35, 0.6),
    ("Margen bruto eventos %", prof("gross_margin", EVENT) * 100, 26, 0.6),
    ("Contrib. margen normal %", prof("contribution_margin", NORMAL) * 100, 26, 0.6),
    ("Contrib. margen eventos %", prof("contribution_margin", EVENT) * 100, 12, 0.6),
    ("Descuento eventos %", prof("discount_rate", EVENT) * 100, 14, 0.5),
    ("Descuento normal %", prof("discount_rate", NORMAL) * 100, 1, 0.5),
    ("Tarde normal %", ops("late_rate", NORMAL) * 100, 11, 1.0),
    ("Tarde eventos %", ops("late_rate", EVENT) * 100, 29, 1.0),
    ("Cancelacion %", one("SELECT SUM(cancel_rate * orders) / SUM(orders) * 100 FROM ecom_sim.vw_ops_by_stage"), 3.5, 0.05),
    ("Devolucion %", one("SELECT SUM(return_rate * orders) / SUM(orders) * 100 FROM ecom_sim.vw_ops_by_stage"), 8.3, 0.05),
]
rows = [(n, float(v), float(e), abs(v - e) <= tol) for n, v, e, tol in CONTROL]
ctl = pd.DataFrame(rows, columns=["control", "view_value", "expected", "passed"])
ctl.to_csv(os.path.join(OUT, "view_control_results.csv"), index=False)
print()
print(ctl.round(4).to_string(index=False))

if len(blocking) or not ctl.passed.all():
    sys.exit("\nVerificacion local FALLIDA")
known = dq[(dq.severity != "blocking") & (~dq.passed)]
print(f"\nVerificacion local OK: {len(dq) - len(known)}/{len(dq)} chequeos pasan, "
      f"{len(known)} limitacion conocida; {len(ctl)} controles coinciden.")
