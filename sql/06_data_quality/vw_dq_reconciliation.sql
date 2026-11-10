-- Pregunta: ¿los numeros cierran entre tablas y vistas?
-- Una fila por chequeo. severity = blocking frena la publicacion;
-- known_limitation queda a la vista y se explica en docs/DATA_QUALITY.md. Datos simulados.
CREATE OR REPLACE VIEW ecom_sim.vw_dq_reconciliation AS
WITH checks AS (
  SELECT 'net_sales_funnel_view_vs_orders' AS check_name, 'blocking' AS severity,
    (SELECT ROUND(SUM(net_sales), 2) FROM ecom_sim.orders WHERE status <> 'cancelled') AS expected,
    (SELECT ROUND(SUM(net_sales), 2) FROM ecom_sim.vw_funnel_daily) AS actual
  UNION ALL SELECT 'orders_funnel_vs_order_rows', 'blocking',
    (SELECT COUNT(*) FROM ecom_sim.orders),
    (SELECT SUM(orders_funnel) FROM ecom_sim.daily_traffic)
  UNION ALL SELECT 'duplicate_order_ids', 'blocking', 0,
    (SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM ecom_sim.orders)
  UNION ALL SELECT 'orders_outside_season', 'blocking', 0,
    (SELECT COUNT(*) FROM ecom_sim.orders WHERE order_date NOT BETWEEN DATE '2025-09-01' AND DATE '2025-12-31')
  UNION ALL SELECT 'variant_b_outside_events', 'blocking', 0,
    (SELECT COUNT(*) FROM ecom_sim.orders WHERE event = 'normal' AND checkout_variant = 'B')
  UNION ALL SELECT 'twelve_installments_in_variant_a', 'blocking', 0,
    (SELECT COUNT(*) FROM ecom_sim.orders WHERE checkout_variant = 'A' AND installments = 12)
  UNION ALL SELECT 'gross_sales_vs_items', 'blocking', 0,
    (SELECT COUNT(*) FROM ecom_sim.orders AS o
     JOIN (SELECT order_id, SUM(list_price * quantity) AS gmv FROM ecom_sim.order_items GROUP BY order_id) AS i
       ON o.order_id = i.order_id
     WHERE ABS(o.gross_sales - i.gmv) > 0.01)
  UNION ALL SELECT 'orders_without_customer', 'blocking', 0,
    (SELECT COUNT(*) FROM ecom_sim.orders AS o LEFT JOIN ecom_sim.customers AS c ON o.customer_id = c.customer_id
     WHERE c.customer_id IS NULL)
  UNION ALL SELECT 'traffic_rows_with_zero_sessions', 'blocking', 0,
    (SELECT COUNT(*) FROM ecom_sim.daily_traffic WHERE sessions = 0)
  UNION ALL SELECT 'funnel_steps_not_decreasing', 'blocking', 0,
    (SELECT COUNT(*) FROM ecom_sim.daily_traffic
     WHERE add_to_cart_sessions > sessions OR checkout_sessions > add_to_cart_sessions OR orders_funnel > checkout_sessions)
  UNION ALL SELECT 'cancelled_with_delivery_date', 'blocking', 0,
    (SELECT COUNT(*) FROM ecom_sim.orders WHERE status = 'cancelled' AND delivered_date IS NOT NULL)
  UNION ALL SELECT 'ab_split_share_off_by_over_1pct', 'blocking', 0,
    (SELECT COUNT(*) FROM (
       SELECT SAFE_DIVIDE(SUM(CASE WHEN checkout_variant = 'A' THEN sessions ELSE 0 END), SUM(sessions)) AS share_a
       FROM ecom_sim.daily_traffic WHERE event <> 'normal') AS s
     WHERE ABS(s.share_a - 0.5) > 0.01)
  UNION ALL SELECT 'item_lines_sold_while_out_of_stock', 'known_limitation', 0,
    (SELECT COUNT(*) FROM ecom_sim.order_items AS i
     JOIN ecom_sim.orders AS o ON i.order_id = o.order_id
     JOIN ecom_sim.daily_stock AS s ON o.order_date = s.date AND i.product_id = s.product_id
     WHERE s.in_stock = 0)
)
SELECT check_name, severity, expected, actual, expected = actual AS passed
FROM checks;
