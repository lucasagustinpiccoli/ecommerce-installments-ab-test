-- Pregunta: ¿el cliente que trae cada canal paga lo que costo traerlo?
-- ltv_observed = contribucion con reembolso de devoluciones / clientes del canal de alta.
-- Es un piso: solo cubre hasta 4 meses de vida. cac = gasto del canal / clientes nuevos.
-- ltv_to_cac queda NULL en canales sin gasto. Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_ltv_cac_by_channel AS
WITH v AS (
  SELECT c.acquisition_channel AS channel, SUM(o.contribution_returns_refunded) AS contribution
  FROM ecom_sim.vw_order_economics AS o
  JOIN ecom_sim.customers AS c ON o.customer_id = c.customer_id
  GROUP BY c.acquisition_channel
), n AS (
  SELECT acquisition_channel AS channel, COUNT(*) AS customers
  FROM ecom_sim.customers
  GROUP BY acquisition_channel
), a AS (
  SELECT channel, SUM(ad_spend) AS ad_spend
  FROM ecom_sim.daily_traffic
  GROUP BY channel
)
SELECT
  n.channel,
  n.customers,
  a.ad_spend,
  SAFE_DIVIDE(v.contribution, n.customers) AS ltv_observed,
  SAFE_DIVIDE(a.ad_spend, CASE WHEN a.ad_spend > 0 THEN n.customers END) AS cac,
  SAFE_DIVIDE(SAFE_DIVIDE(v.contribution, n.customers), SAFE_DIVIDE(a.ad_spend, CASE WHEN a.ad_spend > 0 THEN n.customers END)) AS ltv_to_cac
FROM n
JOIN v ON n.channel = v.channel
JOIN a ON n.channel = a.channel;
