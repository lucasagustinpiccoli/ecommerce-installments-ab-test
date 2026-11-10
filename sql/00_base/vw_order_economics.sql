-- Pregunta: ¿cuanto deja cada pedido, con las dos formas de tratar una devolucion?
-- contribution: net_sales - cogs - payment_fee - financing_cost - envio neto; 0 si se cancelo.
--   Es la definicion del brief: el pedido devuelto conserva su contribucion (optimista).
-- contribution_returns_refunded: igual, pero el devuelto se reembolsa y solo se pierden envio y comision.
-- Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_order_economics AS
SELECT
  o.*,
  o.shipping_cost - o.shipping_charged AS net_shipping_cost,
  CASE WHEN o.status = 'cancelled' THEN 0
       ELSE o.net_sales - o.cogs - o.payment_fee - o.financing_cost - (o.shipping_cost - o.shipping_charged)
  END AS contribution,
  CASE WHEN o.status = 'cancelled' THEN 0
       WHEN o.status = 'returned' THEN -(o.shipping_cost + o.payment_fee)
       ELSE o.net_sales - o.cogs - o.payment_fee - o.financing_cost - (o.shipping_cost - o.shipping_charged)
  END AS contribution_returns_refunded
FROM ecom_sim.orders AS o;
