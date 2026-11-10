-- Pregunta: ¿la diferencia entre variantes se repite en Cyber Monday y en Black Friday?
-- Mismas definiciones que vw_ab_summary, abiertas por evento. Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_ab_by_event AS
WITH t AS (
  SELECT event, checkout_variant, SUM(sessions) AS sessions, SUM(orders_funnel) AS orders, SUM(ad_spend) AS ad_spend
  FROM ecom_sim.daily_traffic
  WHERE event <> 'normal'
  GROUP BY event, checkout_variant
), o AS (
  SELECT event, checkout_variant, SUM(contribution) AS contribution
  FROM ecom_sim.vw_order_economics
  WHERE event <> 'normal'
  GROUP BY event, checkout_variant
)
SELECT
  t.event,
  t.checkout_variant,
  t.sessions,
  t.orders,
  SAFE_DIVIDE(t.orders, t.sessions) AS conversion,
  SAFE_DIVIDE(o.contribution - t.ad_spend, t.sessions) * 1000 AS contribution_after_ads_per_1000_sessions
FROM t
JOIN o ON t.event = o.event AND t.checkout_variant = o.checkout_variant;
