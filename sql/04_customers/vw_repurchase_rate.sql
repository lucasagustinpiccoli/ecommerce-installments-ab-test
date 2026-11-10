-- Pregunta: ¿que parte de los clientes volvio a comprar?
-- repurchase_rate = clientes con 2 o mas pedidos / clientes con pedido (incluye cancelados, como el control).
-- Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_repurchase_rate AS
WITH c AS (
  SELECT customer_id, COUNT(*) AS orders
  FROM ecom_sim.orders
  GROUP BY customer_id
)
SELECT
  COUNT(*) AS customers,
  SUM(CASE WHEN orders >= 2 THEN 1 ELSE 0 END) AS repeat_customers,
  SAFE_DIVIDE(SUM(CASE WHEN orders >= 2 THEN 1 ELSE 0 END), COUNT(*)) AS repurchase_rate
FROM c;
