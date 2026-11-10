-- Pregunta: ¿por que escriben los clientes en cada etapa?
-- contacts_per_100_orders = contactos del motivo / pedidos de la etapa * 100. Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_contacts_by_reason AS
WITH c AS (
  SELECT o.stage, k.reason, COUNT(*) AS contacts
  FROM ecom_sim.contacts AS k
  JOIN ecom_sim.orders AS o ON k.order_id = o.order_id
  GROUP BY o.stage, k.reason
), n AS (
  SELECT stage, COUNT(*) AS orders
  FROM ecom_sim.orders
  GROUP BY stage
)
SELECT
  c.stage,
  c.reason,
  c.contacts,
  SAFE_DIVIDE(c.contacts, n.orders) * 100 AS contacts_per_100_orders
FROM c
JOIN n ON c.stage = n.stage;
