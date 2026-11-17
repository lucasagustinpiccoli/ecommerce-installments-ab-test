# Should an online store offer 12 interest-free installments on Cyber Monday and Black Friday?

**Recommendation: keep 6 installments.** Offering 12 lifts sales per session by 10.6%, but cuts contribution after ads by 35%: about ARS 1.8M given up per 3-day event (95% CI: −0.4M to +4.0M).

> **All data is simulated** (fictional store, seed 42). The effect of installments on conversion and basket size is an assumption of the data generator. This project demonstrates the analysis method, not a finding about real shoppers.

- **Report (2 pages, English):** [docs/report/ecommerce_AB_Test.pdf](docs/report/ecommerce_AB_Test.pdf)
- **Dashboard (Looker Studio, 6 pages):** [open](https://datastudio.google.com/reporting/a4715b0f-c25e-4335-94e4-1e2fbb5f4cf6)

## A/B test results

| Metric | A: up to 6 | B: up to 12 | B vs A | Significant at 95%? |
|---|---|---|---|---|
| Conversion rate | 4.67% | 4.82% | +3.2% (p = 0.245) | No |
| Average order value (ARS) | 67,729 | 72,987 | +7.8% (p = 0.001) | Yes |
| Sales per 1,000 sessions (ARS) | 2.99M | 3.31M | +10.6% | Yes |
| Contribution after ads per 1,000 sessions (ARS) | 95,028 | 61,719 | −35.1% | No, narrowly |

The −35% is not significant on its own, but the decision holds: B needs +12.4% conversion to break even and reached +3.2% (the top of its interval is +8.6%); the test had 99% power to detect that +12.4%; and B is lower in both events.

## Assumptions and limits

The data is simulated, so every result depends on the generator's assumptions. [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md) lists all 26 assumptions with their line in `generate_data.py`, and compares them with public sources (Mercado Pago, the Cuota Simple program, BCRA, CACE as reported by the press, Baymard, IRP Commerce, LocaliQ, Appriss Retail, FMI), each with URL and date.

- **Backed by a source:** cost of 3 and 6 installments (5% and 10%, close to the Cuota Simple caps of 5.41% and 10.31%), payment fee (3%, within Mercado Pago's 1.49% to 6.29%), cart abandonment (72% vs a 70.22% average), share of event orders paid in installments (61% to 65% vs over 60% at Mercado Libre), event-day stockouts (7.5% vs 8.3%).
- **Outside the reference range:** cost of 12 installments (20% vs 32.29% at Mercado Pago), event discounts (20% vs 31%), overall conversion (3.46% vs 1.83% in the UK), event ticket (ARS 70K vs 92K), returns, next-day delivery, search CTR.
- **No source (own assumptions):** the effect of 12 installments on conversion (+8% at checkout) and on basket size, traffic and channel mix, cancellations, margins by category, shipping, repeat purchase.

**Sensitivity:** [scripts/sensitivity.py](scripts/sensitivity.py) varies the three assumptions that drive the decision. Each of these alone, with the other two at their observed values, would make 12 installments break even: a conversion lift of +12.4% (observed +3.2%), the 12-installment cost falling to 13.1% of sales (assumed 20%), or a ticket lift of +14.4% (observed +7.8%). At Mercado Pago's 32.29%, B would need +33.7% conversion. Chart: [docs/report/sensitivity.png](docs/report/sensitivity.png).

## What's in the repo

```
scripts/    generate_data.py, ab_test.py, sensitivity.py, verify_local.py, load_bigquery.sh
sql/        21 BigQuery views by block, explicit schemas and run order
outputs/    test results and data quality checks
docs/       report (English) and full documentation (Spanish)
powerbi/    star schema and DAX measures
```

- **Statistics:** two-proportion z-test, Welch's t-test, session-level bootstrap, break-even conversion, power analysis.
- **Data modelling:** BigQuery with explicit schemas, 21 SQL views, validated in DuckDB against 29 control values.
- **Data quality:** 13 reconciliation checks; 12 pass and the one that fails is documented with its impact.

Stack: Python (pandas, NumPy, SciPy), SQL, BigQuery, DuckDB, Looker Studio, Power BI (DAX).

## Reproduce

```bash
pip install -r requirements.txt
bash run_all.sh
```

`run_all.sh` generates the data, runs the test and the sensitivity analysis, executes the 21 views in DuckDB and checks them against the control values. If `bq` is installed and authenticated, it also loads everything into BigQuery.

## Documentation (Spanish)

- [docs/README.md](docs/README.md): full write-up of the decision
- [docs/METRICS.md](docs/METRICS.md): definition of every metric
- [docs/DATA_QUALITY.md](docs/DATA_QUALITY.md): reconciliations and limitations
- [docs/GUIA_DEL_TABLERO.md](docs/GUIA_DEL_TABLERO.md): page-by-page guide to the dashboard
- [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md): generator assumptions checked against public sources, and sensitivity analysis
