-- Pregunta: ¿cuanto vende y cuanto deja la tienda en toda la temporada, y como se reparte entre eventos y dias comunes?
-- Una fila por periodo: 'Whole season', 'Events (CM + BF)' y 'Regular days'.
-- Trae las sumas para que el tablero recalcule cada tasa como SUM(numerador) / SUM(denominador).
-- conversion = pedidos del embudo / sesiones. ticket = net_sales sin cancelados / pedidos no cancelados.
-- contribution_after_ads = contribucion (definicion del brief) - publicidad.
-- roas_paid = net_sales de pedidos de canales pagos (paid_search, social_ads) / publicidad: el ROAS facturado
--   de vw_acquisition_by_channel, combinado. mer = net_sales de todos los pedidos / publicidad (incluye
--   ventas organicas, directas y por email, por eso es mucho mayor). Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_kpi_overall AS
WITH t AS (
  SELECT
    CASE WHEN event <> 'normal' THEN 'Events (CM + BF)' ELSE 'Regular days' END AS period,
    COUNT(DISTINCT date) AS days,
    SUM(sessions) AS sessions,
    SUM(orders_funnel) AS orders,
    SUM(ad_spend) AS ad_spend
  FROM ecom_sim.daily_traffic
  GROUP BY 1
), o AS (
  SELECT
    CASE WHEN event <> 'normal' THEN 'Events (CM + BF)' ELSE 'Regular days' END AS period,
    SUM(CASE WHEN status <> 'cancelled' THEN net_sales ELSE 0 END) AS net_sales,
    SUM(CASE WHEN status <> 'cancelled' THEN 1 ELSE 0 END) AS orders_not_cancelled,
    SUM(net_sales) AS booked_sales,
    SUM(CASE WHEN channel IN ('paid_search', 'social_ads') THEN net_sales ELSE 0 END) AS paid_booked_sales,
    SUM(contribution) AS contribution
  FROM ecom_sim.vw_order_economics
  GROUP BY 1
), p AS (
  SELECT t.period, t.days, t.sessions, t.orders, t.ad_spend,
         o.net_sales, o.orders_not_cancelled, o.booked_sales, o.paid_booked_sales, o.contribution
  FROM t JOIN o ON t.period = o.period
), s AS (
  SELECT * FROM p
  UNION ALL
  SELECT 'Whole season', SUM(days), SUM(sessions), SUM(orders), SUM(ad_spend),
         SUM(net_sales), SUM(orders_not_cancelled), SUM(booked_sales), SUM(paid_booked_sales), SUM(contribution)
  FROM p
)
SELECT
  period,
  CASE period WHEN 'Whole season' THEN 1 WHEN 'Events (CM + BF)' THEN 2 ELSE 3 END AS period_order,
  days,
  sessions,
  orders,
  orders_not_cancelled,
  net_sales,
  booked_sales,
  paid_booked_sales,
  contribution,
  ad_spend,
  contribution - ad_spend AS contribution_after_ads,
  SAFE_DIVIDE(orders, sessions) AS conversion,
  SAFE_DIVIDE(net_sales, orders_not_cancelled) AS ticket,
  SAFE_DIVIDE(net_sales, sessions) * 1000 AS sales_per_1000_sessions,
  SAFE_DIVIDE(contribution - ad_spend, sessions) * 1000 AS contribution_after_ads_per_1000_sessions,
  SAFE_DIVIDE(paid_booked_sales, ad_spend) AS roas_paid,
  SAFE_DIVIDE(booked_sales, ad_spend) AS mer
FROM s;
