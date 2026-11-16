-- Pregunta: ¿cuanto cuesta entregar tarde?
-- Una fila por tipo de entrega ('On time' / 'Late'), solo pedidos no cancelados (un cancelado nunca llega tarde).
-- Trae las sumas para que el tablero recalcule cada tasa como SUM(numerador) / SUM(denominador):
--   contacts_per_order = contactos / pedidos; csat = suma de puntajes / respuestas; return_rate = devueltos / pedidos.
-- extra_contacts = contactos de los pedidos tarde menos los que habrian tenido con la tasa de los pedidos a tiempo.
-- El costo se mide en contactos y CSAT, no en pesos: los datos no traen el costo de un contacto y no se agrega
-- ese supuesto. Las devoluciones no cambian con la demora (8,5% contra 8,6%). Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_late_delivery_impact AS
WITH k AS (
  SELECT order_id, COUNT(*) AS contacts
  FROM ecom_sim.contacts
  GROUP BY order_id
), s AS (
  SELECT
    CASE WHEN o.is_late = 1 THEN 'Late' ELSE 'On time' END AS delivery,
    COUNT(*) AS orders,
    SUM(COALESCE(k.contacts, 0)) AS contacts,
    SUM(o.csat_score) AS csat_sum,
    COUNT(o.csat_score) AS csat_responses,
    SUM(CASE WHEN o.status = 'returned' THEN 1 ELSE 0 END) AS returned_orders
  FROM ecom_sim.orders AS o
  LEFT JOIN k ON o.order_id = k.order_id
  WHERE o.status <> 'cancelled'
  GROUP BY 1
), base AS (
  SELECT SAFE_DIVIDE(contacts, orders) AS on_time_cpo FROM s WHERE delivery = 'On time'
)
SELECT
  s.delivery,
  CASE s.delivery WHEN 'On time' THEN 1 ELSE 2 END AS delivery_order,
  s.orders,
  s.contacts,
  s.csat_sum,
  s.csat_responses,
  s.returned_orders,
  SAFE_DIVIDE(s.contacts, s.orders) AS contacts_per_order,
  SAFE_DIVIDE(s.csat_sum, s.csat_responses) AS csat,
  SAFE_DIVIDE(s.returned_orders, s.orders) AS return_rate,
  s.contacts - s.orders * base.on_time_cpo AS extra_contacts
FROM s CROSS JOIN base;
