-- Pregunta: ¿que cuotas elige la gente en cada variante y cuanto le cuestan a la tienda?
-- share_orders = pedidos de la cuota / pedidos de la variante, sin cancelados.
-- financing_rate = financing_cost / net_sales. Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_ab_installment_mix AS
SELECT
  checkout_variant,
  installments,
  COUNT(*) AS orders,
  SUM(net_sales) AS net_sales,
  SUM(financing_cost) AS financing_cost,
  SAFE_DIVIDE(COUNT(*), SUM(COUNT(*)) OVER (PARTITION BY checkout_variant)) AS share_orders,
  SAFE_DIVIDE(SUM(financing_cost), SUM(net_sales)) AS financing_rate
FROM ecom_sim.orders
WHERE event <> 'normal' AND status <> 'cancelled'
GROUP BY checkout_variant, installments;
