-- Pregunta: ¿cuantos clientes vuelven a los 30, 60 y 90 dias de su primera compra?
-- Cohorte = mes de alta. Vuelve = pedido no cancelado entre el dia 1 y el dia N desde el alta.
-- Solo entran clientes con N dias observables antes del 2025-12-31: sin esta regla las
-- cohortes nuevas parecen retener menos, solo porque tuvieron menos tiempo. Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_cohort_retention AS
WITH h AS (
  SELECT 30 AS horizon_days UNION ALL SELECT 60 UNION ALL SELECT 90
), e AS (
  SELECT c.customer_id, c.signup_date, h.horizon_days
  FROM ecom_sim.customers AS c
  CROSS JOIN h
  WHERE DATE_ADD(c.signup_date, INTERVAL h.horizon_days DAY) <= DATE '2025-12-31'
), r AS (
  SELECT DISTINCT e.customer_id, e.horizon_days
  FROM e
  JOIN ecom_sim.orders AS o ON e.customer_id = o.customer_id
  WHERE o.status <> 'cancelled'
    AND DATE_DIFF(o.order_date, e.signup_date, DAY) BETWEEN 1 AND e.horizon_days
)
SELECT
  DATE_TRUNC(e.signup_date, MONTH) AS cohort_month,
  e.horizon_days,
  COUNT(*) AS eligible_customers,
  COUNT(r.customer_id) AS retained_customers,
  SAFE_DIVIDE(COUNT(r.customer_id), COUNT(*)) AS retention_rate
FROM e
LEFT JOIN r ON e.customer_id = r.customer_id AND e.horizon_days = r.horizon_days
GROUP BY cohort_month, e.horizon_days;
