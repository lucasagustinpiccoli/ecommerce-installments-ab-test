-- Pregunta: ¿como rinde cada variante de checkout durante los eventos?
-- conversion = pedidos del embudo / sesiones. ticket = net_sales medio sin cancelados.
-- venta y contribucion por 1000 sesiones excluyen cancelados; contribucion descuenta publicidad.
-- Los intervalos y p-valores salen de scripts/ab_test.py (tabla ab_results). Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_ab_summary AS
WITH t AS (
  SELECT checkout_variant, SUM(sessions) AS sessions, SUM(orders_funnel) AS orders, SUM(ad_spend) AS ad_spend
  FROM ecom_sim.daily_traffic
  WHERE event <> 'normal'
  GROUP BY checkout_variant
), o AS (
  SELECT
    checkout_variant,
    SUM(CASE WHEN status <> 'cancelled' THEN net_sales ELSE 0 END) AS net_sales,
    SUM(CASE WHEN status <> 'cancelled' THEN 1 ELSE 0 END) AS orders_not_cancelled,
    SUM(contribution) AS contribution,
    SUM(contribution_returns_refunded) AS contribution_returns_refunded,
    SUM(CASE WHEN status <> 'cancelled' THEN financing_cost ELSE 0 END) AS financing_cost
  FROM ecom_sim.vw_order_economics
  WHERE event <> 'normal'
  GROUP BY checkout_variant
)
SELECT
  t.checkout_variant,
  t.sessions,
  t.orders,
  t.ad_spend,
  o.net_sales,
  o.financing_cost,
  SAFE_DIVIDE(t.orders, t.sessions) AS conversion,
  SAFE_DIVIDE(o.net_sales, o.orders_not_cancelled) AS ticket,
  SAFE_DIVIDE(o.net_sales, t.sessions) * 1000 AS sales_per_1000_sessions,
  SAFE_DIVIDE(o.contribution - t.ad_spend, t.sessions) * 1000 AS contribution_after_ads_per_1000_sessions,
  SAFE_DIVIDE(o.contribution_returns_refunded - t.ad_spend, t.sessions) * 1000 AS contribution_refunded_after_ads_per_1000_sessions,
  SAFE_DIVIDE(o.financing_cost, o.net_sales) AS financing_rate
FROM t
JOIN o ON t.checkout_variant = o.checkout_variant;
