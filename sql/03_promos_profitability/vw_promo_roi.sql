-- Pregunta: ¿el evento deja mas plata que un dia comun, considerando lo que cuesta la promo?
-- baseline: contribucion despues de publicidad promedio por dia de semana en pre y post evento.
-- Se usan las dos etapas para compensar el crecimiento del trafico durante la temporada.
-- incremental = contribucion real - baseline de los mismos dias de semana.
-- promo_roi = incremental / (descuentos + financiacion del evento): cuanto cambia la contribucion por
--   cada peso invertido en la promo. Cyber Monday: -5,26 M / 36,3 M = -14,5%.
-- contribution_vs_baseline = incremental / baseline: cuanto menos deja el evento que dias comunes.
--   Cyber Monday: -5,26 M / 9,15 M = -57,5%. Las dos son correctas; cambia el denominador. Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_promo_roi AS
WITH o AS (
  SELECT
    order_date AS date,
    SUM(contribution) AS contribution,
    SUM(CASE WHEN status <> 'cancelled' THEN discount_amount ELSE 0 END) AS discounts,
    SUM(CASE WHEN status <> 'cancelled' THEN financing_cost ELSE 0 END) AS financing_cost
  FROM ecom_sim.vw_order_economics
  GROUP BY order_date
), a AS (
  SELECT date, SUM(ad_spend) AS ad_spend
  FROM ecom_sim.daily_traffic
  GROUP BY date
), d AS (
  SELECT
    k.date,
    k.event,
    k.stage,
    k.day_of_week,
    o.contribution - a.ad_spend AS contribution_after_ads,
    o.discounts,
    o.financing_cost
  FROM ecom_sim.vw_dim_calendar AS k
  JOIN o ON k.date = o.date
  JOIN a ON k.date = a.date
), base AS (
  SELECT day_of_week, AVG(contribution_after_ads) AS baseline
  FROM d
  WHERE stage IN ('1_pre_evento', '5_post_evento')
  GROUP BY day_of_week
)
SELECT
  d.event,
  CASE d.event WHEN 'cyber_monday' THEN 'Cyber Monday' ELSE 'Black Friday' END AS event_label,
  SUM(d.contribution_after_ads) AS contribution_after_ads,
  SUM(b.baseline) AS baseline_same_weekdays,
  SUM(d.contribution_after_ads) - SUM(b.baseline) AS incremental_contribution,
  SUM(d.discounts) + SUM(d.financing_cost) AS promo_cost,
  SAFE_DIVIDE(SUM(d.contribution_after_ads) - SUM(b.baseline), SUM(d.discounts) + SUM(d.financing_cost)) AS promo_roi,
  SAFE_DIVIDE(SUM(d.contribution_after_ads) - SUM(b.baseline), SUM(b.baseline)) AS contribution_vs_baseline,
  CASE d.event WHEN 'cyber_monday' THEN 1 ELSE 2 END AS event_order
FROM d
JOIN base AS b ON d.day_of_week = b.day_of_week
WHERE d.event <> 'normal'
GROUP BY d.event, event_label, event_order;
