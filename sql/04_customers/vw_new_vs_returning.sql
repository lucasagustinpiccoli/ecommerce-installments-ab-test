-- Pregunta: ¿cuanto de cada etapa viene de clientes nuevos y cuanto de recurrentes?
-- Pedidos no cancelados, segun is_returning_customer. Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_new_vs_returning AS
SELECT
  stage,
  CASE WHEN is_returning_customer = 1 THEN 'returning' ELSE 'new' END AS customer_type,
  COUNT(*) AS orders,
  SUM(net_sales) AS net_sales,
  SAFE_DIVIDE(SUM(net_sales), COUNT(*)) AS ticket
FROM ecom_sim.orders
WHERE status <> 'cancelled'
GROUP BY stage, customer_type;
