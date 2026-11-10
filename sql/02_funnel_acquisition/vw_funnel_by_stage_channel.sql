-- Pregunta: ¿donde se pierde gente en cada etapa y canal?
-- bounce_rate = rebotes / sesiones. add_to_cart_rate = carritos / sesiones.
-- conversion = pedidos / sesiones. cart_abandonment = 1 - pedidos / carritos.
-- revenue_per_visit = ventas netas sin cancelados / sesiones. Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_funnel_by_stage_channel AS
SELECT
  stage,
  channel,
  SUM(sessions) AS sessions,
  SUM(add_to_cart_sessions) AS add_to_cart_sessions,
  SUM(checkout_sessions) AS checkout_sessions,
  SUM(orders_funnel) AS orders,
  SAFE_DIVIDE(SUM(bounced_sessions), SUM(sessions)) AS bounce_rate,
  SAFE_DIVIDE(SUM(add_to_cart_sessions), SUM(sessions)) AS add_to_cart_rate,
  SAFE_DIVIDE(SUM(checkout_sessions), SUM(add_to_cart_sessions)) AS cart_to_checkout_rate,
  SAFE_DIVIDE(SUM(orders_funnel), SUM(sessions)) AS conversion,
  1 - SAFE_DIVIDE(SUM(orders_funnel), SUM(add_to_cart_sessions)) AS cart_abandonment,
  SAFE_DIVIDE(SUM(net_sales), SUM(sessions)) AS revenue_per_visit
FROM ecom_sim.vw_funnel_daily
GROUP BY stage, channel;
