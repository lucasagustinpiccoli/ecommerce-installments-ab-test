-- Pregunta: ¿que clientes conviene cuidar, recuperar o dejar ir?
-- Recencia al 2025-12-31, frecuencia y monto sobre pedidos no cancelados; cada dimension en quintiles (5 = mejor).
-- La mayoria tiene un solo pedido, por eso la frecuencia desempata por monto. Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_customer_rfm AS
WITH c AS (
  SELECT
    customer_id,
    DATE_DIFF(DATE '2025-12-31', MAX(order_date), DAY) AS recency_days,
    COUNT(*) AS frequency,
    SUM(net_sales) AS monetary
  FROM ecom_sim.orders
  WHERE status <> 'cancelled'
  GROUP BY customer_id
), s AS (
  SELECT
    c.*,
    NTILE(5) OVER (ORDER BY recency_days DESC, customer_id) AS r_score,
    NTILE(5) OVER (ORDER BY frequency, monetary, customer_id) AS f_score,
    NTILE(5) OVER (ORDER BY monetary, customer_id) AS m_score
  FROM c
)
SELECT
  s.*,
  CASE
    WHEN r_score >= 4 AND f_score >= 4 THEN 'champions'
    WHEN f_score >= 4 THEN 'at_risk_loyal'
    WHEN r_score >= 4 THEN 'recent'
    ELSE 'dormant'
  END AS segment
FROM s;
