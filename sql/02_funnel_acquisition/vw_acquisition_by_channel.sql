-- Pregunta: ¿cuanto cuesta y cuanto devuelve cada canal?
-- ctr = clics / impresiones. cpc = gasto / clics. cac = gasto / clientes nuevos del canal.
-- roas_booked = ventas netas de todos los pedidos / gasto (es el ROAS de control del brief).
-- roas_realized cuenta solo pedidos entregados y no devueltos: es el mas exigente.
-- Canales sin gasto quedan en NULL. Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_acquisition_by_channel AS
WITH t AS (
  SELECT channel, SUM(sessions) AS sessions, SUM(impressions) AS impressions, SUM(clicks) AS clicks, SUM(ad_spend) AS ad_spend
  FROM ecom_sim.daily_traffic
  GROUP BY channel
), o AS (
  SELECT
    channel,
    COUNT(*) AS orders,
    SUM(net_sales) AS booked_sales,
    SUM(CASE WHEN status = 'delivered' THEN net_sales ELSE 0 END) AS realized_sales
  FROM ecom_sim.orders
  GROUP BY channel
), c AS (
  SELECT acquisition_channel AS channel, COUNT(*) AS new_customers
  FROM ecom_sim.customers
  GROUP BY acquisition_channel
)
SELECT
  t.channel,
  t.sessions,
  t.ad_spend,
  o.orders,
  c.new_customers,
  SAFE_DIVIDE(t.clicks, NULLIF(t.impressions, 0)) AS ctr,
  SAFE_DIVIDE(t.ad_spend, NULLIF(t.clicks, 0)) AS cpc,
  SAFE_DIVIDE(t.ad_spend, CASE WHEN t.ad_spend > 0 THEN c.new_customers END) AS cac,
  SAFE_DIVIDE(o.booked_sales, NULLIF(t.ad_spend, 0)) AS roas_booked,
  SAFE_DIVIDE(o.realized_sales, NULLIF(t.ad_spend, 0)) AS roas_realized,
  SAFE_DIVIDE(o.booked_sales, t.sessions) AS revenue_per_visit
FROM t
JOIN o ON t.channel = o.channel
JOIN c ON t.channel = c.channel;
