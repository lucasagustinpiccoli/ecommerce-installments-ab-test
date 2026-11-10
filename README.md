# Should an online store offer 12 interest-free installments on Cyber Monday and Black Friday?

**Recommendation: keep 6 installments.** Offering 12 lifts sales per session by 10.6%, but cuts contribution after ads by 35%: about ARS 1.8M given up per 3-day event (95% CI: −0.4M to +4.0M).

> **All data is simulated** (fictional store, seed 42). The effect of installments on conversion and basket size is an assumption of the data generator. This project demonstrates the analysis method, not a finding about real shoppers.

- **Report (2 pages, English):** [docs/report/Lucas_Piccoli_12_Installments_AB_Test.pdf](docs/report/Lucas_Piccoli_12_Installments_AB_Test.pdf)
- **Dashboard (Looker Studio, 6 pages):** [open](https://datastudio.google.com/reporting/a4715b0f-c25e-4335-94e4-1e2fbb5f4cf6)

## A/B test results

| Metric | A: up to 6 | B: up to 12 | B vs A | Significant at 95%? |
|---|---|---|---|---|
| Conversion rate | 4.67% | 4.82% | +3.2% (p = 0.245) | No |
| Average order value (ARS) | 67,729 | 72,987 | +7.8% (p = 0.001) | Yes |
| Sales per 1,000 sessions (ARS) | 2.99M | 3.31M | +10.6% | Yes |
| Contribution after ads per 1,000 sessions (ARS) | 95,028 | 61,719 | −35.1% | No, narrowly |

The −35% is not significant on its own, but the decision holds: B needs +12.4% conversion to break even and reached +3.2% (the top of its interval is +8.6%); the test had 99% power to detect that +12.4%; and B is lower in both events.

## What's in the repo

```
scripts/    generate_data.py, ab_test.py, verify_local.py, load_bigquery.sh
sql/        19 BigQuery views by block, explicit schemas and run order
outputs/    test results and data quality checks
docs/       report (English) and full documentation (Spanish)
powerbi/    star schema and DAX measures
```

- **Statistics:** two-proportion z-test, Welch's t-test, session-level bootstrap, break-even conversion, power analysis.
- **Data modelling:** BigQuery with explicit schemas, 19 SQL views, validated in DuckDB against 22 control values.
- **Data quality:** 13 reconciliation checks; 12 pass and the one that fails is documented with its impact.

Stack: Python (pandas, NumPy, SciPy), SQL, BigQuery, DuckDB, Looker Studio, Power BI (DAX).

## Reproduce

```bash
pip install -r requirements.txt
bash run_all.sh
```

`run_all.sh` generates the data, runs the test, executes the 19 views in DuckDB and checks them against the control values. If `bq` is installed and authenticated, it also loads everything into BigQuery.

## Documentation (Spanish)

- [docs/README.md](docs/README.md): full write-up of the decision
- [docs/METRICS.md](docs/METRICS.md): definition of every metric
- [docs/DATA_QUALITY.md](docs/DATA_QUALITY.md): reconciliations and limitations
- [docs/GUIA_DEL_TABLERO.md](docs/GUIA_DEL_TABLERO.md): page-by-page guide to the dashboard
