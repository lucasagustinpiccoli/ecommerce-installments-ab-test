-- Pregunta: ¿cuanta gente pasa por cada paso del embudo, por dia, canal y variante?
-- Base del dashboard: guarda conteos, no tasas. En Looker y Power BI cada tasa se calcula
-- como SUM(numerador) / SUM(denominador); promediar tasas diarias daria un valor incorrecto.
-- net_sales incluye los pedidos no cancelados de esa fecha, canal y variante. Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_funnel_daily AS
WITH s AS (
  SELECT order_date, channel, checkout_variant, SUM(net_sales) AS net_sales
  FROM ecom_sim.orders
  WHERE status <> 'cancelled'
  GROUP BY order_date, channel, checkout_variant
)
SELECT
  t.*,
  COALESCE(s.net_sales, 0) AS net_sales
FROM ecom_sim.daily_traffic AS t
LEFT JOIN s
  ON t.date = s.order_date AND t.channel = s.channel AND t.checkout_variant = s.checkout_variant;
