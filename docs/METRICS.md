# Definición de métricas

Datos simulados. Montos en pesos argentinos simulados.

**Regla para cualquier dashboard:** una tasa se calcula como `SUM(numerador) / SUM(denominador)` en el nivel que se muestra. Promediar tasas ya calculadas da un valor incorrecto.

## Test A/B

| Métrica | Fórmula | Fuente | Qué la haría incorrecta |
|---|---|---|---|
| Conversión | pedidos del embudo / sesiones | `vw_ab_summary` | Incluir días fuera de eventos, cuando todas las sesiones son A |
| Ticket | net_sales promedio sin cancelados | `vw_ab_summary` | Incluir cancelados o usar solo entregados: daría otro número que el control |
| Venta por 1.000 sesiones | net_sales sin cancelados / sesiones × 1.000 | `vw_ab_summary` | Dividir por pedidos en lugar de sesiones |
| Contribución después de publicidad por 1.000 sesiones | (contribución - ad_spend) / sesiones × 1.000 | `vw_ab_summary` | Omitir la publicidad o el costo de financiación |
| Ídem con reembolso | igual, con `contribution_returns_refunded` | `vw_ab_summary` | Tratarla como el valor base en lugar de un escenario |
| IC y p-valor | proporciones, Welch y bootstrap por sesión | `ab_results`, `scripts/ab_test.py` | Hacer bootstrap solo sobre pedidos: ignora la incertidumbre de la conversión |
| Punto de equilibrio | conversión con la que B iguala la contribución de A | `outputs/ab_results.json` | Comparar contra la conversión sin mantener la contribución por pedido de B |
| Poder y MDE | prueba de dos proporciones, α 5%, poder 80% | `outputs/ab_results.json` | Leer "+3%" como puntos porcentuales: es relativo |

## Contribución: dos definiciones por pedido

| Estado | `contribution` (brief) | `contribution_returns_refunded` |
|---|---|---|
| Entregado | net_sales - cogs - payment_fee - financing_cost - envío neto | Igual |
| Devuelto | Igual que entregado | -(shipping_cost + payment_fee) |
| Cancelado | 0 | 0 |

Envío neto = shipping_cost - shipping_charged. Fuente: `vw_order_economics`.

La primera es optimista, porque asume que no se reembolsa una venta devuelta. La segunda asume que la tienda recupera la mercadería en condiciones de venderla. La realidad debería estar entre ambas, y la conclusión es la misma con las dos.

## Embudo y adquisición

| Métrica | Fórmula | Fuente | Qué la haría incorrecta |
|---|---|---|---|
| Tasa de rebote | bounced_sessions / sessions | `vw_funnel_daily` | Promediar tasas diarias |
| Tasa de carrito | add_to_cart_sessions / sessions | `vw_funnel_daily` | Ídem |
| Abandono de carrito | 1 - pedidos / add_to_cart_sessions | `vw_funnel_by_stage_channel` | Usar sesiones de checkout como denominador |
| CTR | clicks / impressions | `vw_acquisition_by_channel` | Incluir canales sin impresiones |
| CPC | ad_spend / clicks | `vw_acquisition_by_channel` | Ídem |
| CAC | ad_spend / clientes nuevos del canal | `vw_acquisition_by_channel` | Contar pedidos en lugar de clientes nuevos |
| ROAS facturado | net_sales de todos los pedidos / ad_spend | `vw_acquisition_by_channel` | Es el del control e incluye cancelados y devueltos |
| ROAS realizado | net_sales entregados no devueltos / ad_spend | `vw_acquisition_by_channel` | Compararlo con un ROAS facturado de otra fuente |
| Ingreso por visita | net_sales / sessions | `vw_funnel_by_stage_channel` | Las dos vistas difieren: una excluye cancelados y la otra no |

## Promos y rentabilidad

`vw_profitability_by_stage` usa **solo pedidos entregados**, como los valores de control. El A/B usa pedidos no cancelados. Por eso el ticket global (~77.000) y el de eventos no se comparan directamente.

| Métrica | Fórmula | Fuente | Qué la haría incorrecta |
|---|---|---|---|
| GMV | SUM(gross_sales) | `vw_profitability_by_stage` | Confundirlo con ventas netas |
| Tasa de descuento | discounts / GMV | `vw_profitability_by_stage` | Dividir por ventas netas |
| Margen bruto | (net_sales - cogs) / net_sales | `vw_profitability_by_stage` | Dividir por GMV |
| Margen de contribución | (net_sales - cogs - payment_fee - financing_cost - envío neto) / net_sales | `vw_profitability_by_stage` | Olvidar que es antes de publicidad |
| ROI de promo | (contribución después de ads - baseline) / (descuentos + financiación) | `vw_promo_roi` | Usar un baseline sin ajustar por día de semana, o solo de la etapa previa |

El baseline promedia por día de semana las etapas pre y post evento, lo que compensa el crecimiento del tráfico durante la temporada.

## Clientes

| Métrica | Fórmula | Fuente | Qué la haría incorrecta |
|---|---|---|---|
| Recompra | clientes con 2+ pedidos / clientes | `vw_repurchase_rate` | Contar pedidos recurrentes en lugar de clientes |
| Retención 30/60/90 | clientes con pedido entre el día 1 y N / clientes elegibles | `vw_cohort_retention` | Incluir clientes sin N días observables |
| LTV observado | contribución con reembolso / clientes del canal de alta | `vw_ltv_cac_by_channel` | Leerlo como vida completa: cubre 4 meses como máximo |
| LTV/CAC | LTV observado / CAC | `vw_ltv_cac_by_channel` | Aplicarlo a canales sin gasto |
| RFM | quintiles de recencia, frecuencia y monto | `vw_customer_rfm` | Usar umbrales fijos: casi todos tienen un pedido |

## Operaciones

| Métrica | Fórmula | Fuente | Qué la haría incorrecta |
|---|---|---|---|
| Entregas tarde | is_late / pedidos no cancelados | `vw_ops_by_stage` | Usar todos los pedidos: da 13,4% en lugar de 13,9% |
| p50 y p90 de entrega | percentil de días entre pedido y entrega | `vw_ops_by_stage` | Promediar percentiles entre etapas |
| Cancelación y devolución | pedidos en ese estado / todos los pedidos | `vw_ops_by_stage` | Calcular devoluciones sobre entregados sin aclararlo |
| Quiebre de stock | producto-días sin stock / producto-días | `vw_stockouts_by_stage` | Leerlo como ventas perdidas: los datos no las registran |
| Contactos por pedido | contactos / pedidos | `vw_ops_by_stage` | Asignar el contacto a su fecha y no a la etapa del pedido |
| CSAT | promedio de csat_score | `vw_ops_by_stage` | Olvidar que responde ~25% de las entregas |
