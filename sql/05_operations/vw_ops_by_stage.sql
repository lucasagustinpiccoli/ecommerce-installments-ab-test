-- Pregunta: ¿la operacion aguanta el pico de los eventos?
-- late_rate y on_time_rate: denominador = pedidos no cancelados (un cancelado nunca llega tarde).
-- p50 y p90: dias entre pedido y entrega. cancel_rate y return_rate: sobre todos los pedidos.
-- contacts_per_order = contactos / pedidos. csat = promedio de las respuestas (~25% de entregas).
-- Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_ops_by_stage AS
WITH p AS (
  SELECT
    stage,
    PERCENTILE_CONT(DATE_DIFF(delivered_date, order_date, DAY), 0.5) OVER (PARTITION BY stage) AS p50,
    PERCENTILE_CONT(DATE_DIFF(delivered_date, order_date, DAY), 0.9) OVER (PARTITION BY stage) AS p90
  FROM ecom_sim.orders
  WHERE delivered_date IS NOT NULL
), q AS (
  SELECT stage, MAX(p50) AS p50_delivery_days, MAX(p90) AS p90_delivery_days
  FROM p
  GROUP BY stage
), k AS (
  SELECT o.stage, COUNT(*) AS contacts
  FROM ecom_sim.contacts AS c
  JOIN ecom_sim.orders AS o ON c.order_id = o.order_id
  GROUP BY o.stage
), o AS (
  SELECT
    stage,
    COUNT(*) AS orders,
    SUM(CASE WHEN status <> 'cancelled' THEN 1 ELSE 0 END) AS shipped_orders,
    SUM(is_late) AS late_orders,
    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
    SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END) AS returned_orders,
    AVG(csat_score) AS csat
  FROM ecom_sim.orders
  GROUP BY stage
)
SELECT
  o.stage,
  o.orders,
  SAFE_DIVIDE(o.late_orders, o.shipped_orders) AS late_rate,
  1 - SAFE_DIVIDE(o.late_orders, o.shipped_orders) AS on_time_rate,
  q.p50_delivery_days,
  q.p90_delivery_days,
  SAFE_DIVIDE(o.cancelled_orders, o.orders) AS cancel_rate,
  SAFE_DIVIDE(o.returned_orders, o.orders) AS return_rate,
  SAFE_DIVIDE(k.contacts, o.orders) AS contacts_per_order,
  o.csat
FROM o
JOIN q ON o.stage = q.stage
JOIN k ON o.stage = k.stage;
