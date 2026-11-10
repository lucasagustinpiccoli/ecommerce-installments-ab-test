-- Pregunta: ¿cuanto margen se resigna en cada etapa de la temporada?
-- Solo pedidos delivered: asi se calculan los valores de control del brief.
-- discount_rate = descuentos / GMV. gross_margin = (ventas - cogs) / ventas.
-- contribution_margin = (ventas - cogs - comision - financiacion - envio neto) / ventas, antes de publicidad.
-- Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_profitability_by_stage AS
WITH o AS (
  SELECT
    stage,
    COUNT(*) AS orders,
    SUM(gross_sales) AS gmv,
    SUM(discount_amount) AS discounts,
    SUM(net_sales) AS net_sales,
    SUM(cogs) AS cogs,
    SUM(payment_fee) AS payment_fees,
    SUM(financing_cost) AS financing_cost,
    SUM(net_shipping_cost) AS net_shipping_cost
  FROM ecom_sim.vw_order_economics
  WHERE status = 'delivered'
  GROUP BY stage
), t AS (
  SELECT stage, SUM(ad_spend) AS ad_spend
  FROM ecom_sim.daily_traffic
  GROUP BY stage
)
SELECT
  o.*,
  t.ad_spend,
  SAFE_DIVIDE(o.discounts, o.gmv) AS discount_rate,
  SAFE_DIVIDE(o.net_sales - o.cogs, o.net_sales) AS gross_margin,
  SAFE_DIVIDE(o.financing_cost, o.net_sales) AS financing_rate,
  SAFE_DIVIDE(o.net_sales - o.cogs - o.payment_fees - o.financing_cost - o.net_shipping_cost, o.net_sales) AS contribution_margin
FROM o
JOIN t ON o.stage = t.stage;
