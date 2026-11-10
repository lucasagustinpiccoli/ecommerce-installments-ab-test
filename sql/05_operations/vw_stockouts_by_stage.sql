-- Pregunta: ¿cuantos productos estuvieron sin stock en cada etapa y categoria?
-- stockout_rate = producto-dias sin stock / producto-dias. Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_stockouts_by_stage AS
SELECT
  k.stage,
  p.category,
  COUNT(*) AS product_days,
  SUM(1 - s.in_stock) AS out_of_stock_days,
  SAFE_DIVIDE(SUM(1 - s.in_stock), COUNT(*)) AS stockout_rate
FROM ecom_sim.daily_stock AS s
JOIN ecom_sim.products AS p ON s.product_id = p.product_id
JOIN ecom_sim.vw_dim_calendar AS k ON s.date = k.date
GROUP BY k.stage, p.category;
