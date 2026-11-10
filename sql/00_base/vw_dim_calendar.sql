-- Pregunta: ¿que evento, etapa y dia de semana tiene cada fecha?
-- Dimension calendario del modelo en estrella. Una fila por fecha. day_of_week: 1 = domingo.
CREATE OR REPLACE VIEW ecom_sim.vw_dim_calendar AS
SELECT DISTINCT
  date,
  event,
  stage,
  EXTRACT(DAYOFWEEK FROM date) AS day_of_week,
  EXTRACT(MONTH FROM date) AS month_number,
  event <> 'normal' AS is_event
FROM ecom_sim.daily_traffic;
