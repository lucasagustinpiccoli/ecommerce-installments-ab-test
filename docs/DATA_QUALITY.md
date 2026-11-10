# Calidad de datos

Datos simulados. Resultado de `run_all.sh` con seed 42. Los 13 chequeos se ejecutaron en BigQuery y en DuckDB, con el mismo resultado. Los 22 valores de control se comparan en DuckDB.

**Resultado:** 12 de 13 chequeos pasan, 1 limitación conocida queda a la vista y los 22 valores de control coinciden. Los 7 CSV regenerados son idénticos a los del brief.

## Reconciliaciones

Fuente: `vw_dq_reconciliation`. El detalle queda en `outputs/data_quality_results.csv`.

| Chequeo | Esperado | Obtenido | Resultado |
|---|---|---|---|
| Ventas netas de la vista = suma de `orders` | 2.808.863.355,17 | Igual | Pasa |
| Pedidos del embudo = filas de `orders` | 37.861 | 37.861 | Pasa |
| `order_id` duplicados | 0 | 0 | Pasa |
| Pedidos fuera de temporada | 0 | 0 | Pasa |
| Variante B fuera de eventos | 0 | 0 | Pasa |
| 12 cuotas en variante A | 0 | 0 | Pasa |
| `gross_sales` distinto de la suma de ítems | 0 | 0 | Pasa |
| Pedidos sin cliente | 0 | 0 | Pasa |
| Filas de tráfico con 0 sesiones | 0 | 0 | Pasa |
| Pasos del embudo que crecen | 0 | 0 | Pasa |
| Cancelados con fecha de entrega | 0 | 0 | Pasa |
| Reparto A/B desviado más de 1 punto de 50% | 0 | 0 | Pasa |
| **Líneas vendidas sin stock** | **0** | **1.809** | **Limitación conocida** |

## Registro de errores atrapados

Son hallazgos reales del armado del proyecto.

### 1. Se vendieron productos sin stock

El generador sortea `daily_stock` de forma independiente de los pedidos. Por eso hay 1.809 líneas de pedido (2,97%), en 1.755 pedidos, sobre productos marcados sin stock ese día. El problema es más frecuente en eventos (6%) que en días normales (2,4%).

**Qué se hizo:** no se tocaron los datos validados. El chequeo queda visible como `known_limitation` y se midió su efecto en el test. Afecta más a B (10,7% de pedidos) que a A (8,8%), porque B lleva más ítems por pedido. Al excluir esos pedidos, la contribución por 1.000 sesiones queda en 57.293 para A y 16.571 para B, así que la conclusión no cambia.

**Consecuencia:** `vw_stockouts_by_stage` muestra disponibilidad, pero no sirve para estimar ventas perdidas.

### 2. La contribución base no descuenta las devoluciones

Un pedido devuelto conserva toda su contribución en la definición del brief y del generador. El test excluye solo cancelados. Eso infla la contribución de ambas variantes: A pasa de 26.920 a 95.028 por 1.000 sesiones.

**Qué se hizo:** se mantuvo la definición del brief para reproducir el control y se agregó `contribution_returns_refunded` como escenario. Con reembolso, B queda en -5.023.

### 3. `csat_score` llega como decimal

La columna tiene nulos, así que pandas la escribe como `4.0`. Con un schema `INT64`, se esperaría que BigQuery rechace esos valores.

**Qué se hizo:** el schema la declara `FLOAT64`, y la carga a BigQuery funcionó. No se probó la carga con `INT64`, así que el rechazo es lo esperado, no algo observado.

### 4. El orden alfabético rompía la creación de vistas

`vw_funnel_by_stage_channel` depende de `vw_funnel_daily`, pero se creaba antes y la verificación falló.

**Qué se hizo:** `sql/views_order.txt` fija el orden. `verify_local.py` falla si una vista no figura ahí.

## Revisado y sin error

- **Fechas posteriores al 31/12:** 1.030 entregas y 86 contactos ocurren después del cierre. Son consecuencia lógica de pedidos de fin de diciembre, así que el chequeo de rango aplica solo a `order_date`.
- **Nulos:** `delivered_date` falta solo en cancelados. `csat_score` falta en quienes no respondieron.
- **Primera compra:** coincide con `signup_date` en todos los clientes, y `is_returning_customer` coincide con el orden real de pedidos.
- **p-valor de conversión:** da 0,245, y el brief redondea a ≈0,25. El control usa una tolerancia de 0,01.

## Limitaciones del dato simulado

- **LTV casi igual por canal:** ronda los 19.200 ARS en los cinco canales, porque el generador no diferencia el valor del cliente según el canal. No hay que sacar conclusiones de esa igualdad.
- **Retención por cohorte:** las cohortes tardías tienen pocos clientes elegibles. Octubre a 90 días tiene 436 y noviembre a 60 días tiene 212. El dashboard debería ocultar celdas con menos de 1.000.
- **LTV/CAC por debajo de 1** (0,82 en búsqueda y 0,58 en social) cubre 4 meses como máximo, así que es un piso.

## Supuestos del generador

| Supuesto | Valor |
|---|---|
| Mejora de conversión en checkout de B | +8% sobre la probabilidad de comprar en el checkout |
| Ítems por pedido en B | Media de ítems extra 0,75 contra 0,60 |
| Mix de cuotas en eventos | A: 40/22/38% (1/3/6). B: 35/20/30/15% (1/3/6/12) |
| Costo de financiación | 0%, 5%, 10% y 20% de la venta neta |
| Tráfico en eventos | ×2,2 en Cyber Monday, ×2,0 en Black Friday |
| Comisión de pago | 3% |
