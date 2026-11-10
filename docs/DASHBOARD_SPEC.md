# Especificación del dashboard (6 páginas)

Para armar en Looker Studio sobre BigQuery y en Power BI. Audiencia: gerente o hiring manager.

Los nombres en `este formato` son los campos exactos de cada fuente, como aparecen en Looker Studio.

## Reglas para todas las páginas

- **Idioma:** todo lo visible en el dashboard va en inglés, con punto decimal (10.6%). Looker Studio no traduce las páginas.
- **Título:** dice la conclusión, no el tema.
- **Rótulo fijo:** "Simulated data. Fictional store." visible en cada página.
- **Filtros:** solo funcionan si la fuente tiene ese campo. Ver "Qué filtros admite cada fuente".
- **Tasas:** en `vw_funnel_daily`, crear campos calculados `SUM(numerador) / SUM(denominador)`. Nunca usar el promedio de una tasa.
- **Tasas ya calculadas:** las otras vistas traen tasas listas, con una fila por categoría. Mostrarlas por categoría, con agregación AVG y sin fila de totales.
- **Moneda:** ARS sin decimales, con "M" para millones.

### Colores

| Elemento | Color |
|---|---|
| 1_pre_evento | `#94A3B8` |
| 2_cyber_monday | `#2563EB` |
| 3_entre_eventos | `#CBD5E1` |
| 4_black_friday | `#111827` |
| 5_post_evento | `#64748B` |
| Variante A | `#0F766E` |
| Variante B | `#EA580C` |

Mantener los colores de A y B en todo el dashboard.

### Valores de los datos en inglés

Las etapas y los motivos de contacto vienen en español desde los datos. En Looker Studio, crear estos campos calculados en cada fuente que los use y mostrarlos en lugar de los originales.

**Stage label** (campo `stage`). Va en `vw_profitability_by_stage`, `vw_new_vs_returning`, `vw_ops_by_stage`, `vw_stockouts_by_stage` y `vw_contacts_by_reason`:

```
CASE stage
  WHEN "1_pre_evento" THEN "1. Pre-event"
  WHEN "2_cyber_monday" THEN "2. Cyber Monday"
  WHEN "3_entre_eventos" THEN "3. Between events"
  WHEN "4_black_friday" THEN "4. Black Friday"
  WHEN "5_post_evento" THEN "5. Post-event"
END
```

**Reason label** (campo `reason`, en `vw_contacts_by_reason`):

```
CASE reason
  WHEN "devolucion" THEN "Return"
  WHEN "cancelacion" THEN "Cancellation"
  WHEN "demora_entrega" THEN "Late delivery"
  WHEN "consulta_general" THEN "General inquiry"
END
```

Renombrar también las métricas de cada gráfico con nombres legibles, por ejemplo `Conversion rate` en lugar de `conversion`.

### Fuentes de datos

Conectar en Looker Studio: `vw_funnel_daily`, `vw_ab_summary`, `vw_ab_by_event`, `vw_ab_installment_mix`, `ab_results`, `vw_profitability_by_stage`, `vw_promo_roi`, `vw_acquisition_by_channel`, `vw_cohort_retention`, `vw_ltv_cac_by_channel`, `vw_new_vs_returning`, `vw_ops_by_stage`, `vw_stockouts_by_stage`, `vw_contacts_by_reason`, `vw_dq_reconciliation`.

### Qué filtros admite cada fuente

| Fuente | Fecha | Etapa | Canal |
|---|---|---|---|
| `vw_funnel_daily` | Sí (`date`) | Sí (`stage`) | Sí (`channel`) |
| `vw_profitability_by_stage`, `vw_new_vs_returning`, `vw_ops_by_stage`, `vw_stockouts_by_stage`, `vw_contacts_by_reason` | No | Sí (`stage`) | No |
| `vw_acquisition_by_channel`, `vw_ltv_cac_by_channel` | No | No | Sí (`channel`) |
| Fuentes del A/B, `vw_promo_roi`, `vw_cohort_retention`, `vw_dq_reconciliation` | No | No | No |

Un filtro no afecta a las fuentes que no tienen ese campo. Por eso, en cada página, agregar solo los filtros de la columna "Filtros".

| Página | Filtros |
|---|---|
| 1 | Ninguno |
| 2 | Ninguno: el test cubre solo los eventos |
| 3 | Ninguno |
| 4 | `channel` sobre `vw_funnel_daily`, y aclarar qué gráficos afecta |
| 5 | `stage` |
| 6 | Ninguno |

## Guía de diseño

**Idea general:** fondo claro, poco color y mucho aire. El color se reserva para lo que compara o decide: las variantes A y B, y los eventos. Todo lo demás va en grises.

### Configuración inicial

En **Theme and layout**:

- **Canvas:** 1200 × 900 px. Si una página no entra, aumentar solo la altura.
- **Grid:** márgenes de 24 px y 16 px entre bloques.
- **Fuente:** Roboto en todo el informe.
- **Rótulo, número de página y navegación:** crearlos una vez, hacer clic derecho y elegir **Make report-level**. Así aparecen en todas las páginas y se editan en un solo lugar.

### Paleta de la página

| Elemento | Color |
|---|---|
| Fondo de la página | `#F8FAFC` |
| Fondo de gráficos y tablas | `#FFFFFF` |
| Bordes y líneas de la grilla | `#E2E8F0` |
| Texto principal | `#0F172A` |
| Texto secundario, ejes y notas | `#475569` |
| Fondo del bloque de recomendación | `#F0FDFA` |
| Encabezado de tablas | `#F1F5F9` |

Los colores de datos son los de la sección "Colores" de arriba. No agregar otros: A y B tienen que reconocerse en todas las páginas.

### Títulos y textos

| Elemento | Tamaño | Estilo | Color |
|---|---|---|---|
| Título de la página | 26 px | Negrita | `#0F172A` |
| Bajada debajo del título | 14 px | Normal | `#475569` |
| Título de cada gráfico | 14 px | Negrita | `#0F172A` |
| Tablas y ejes | 12 px | Normal | `#475569` |
| Notas al pie y rótulo | 11 px | Normal | `#475569` |

- **Título de la página:** alineado a la izquierda, en una o dos líneas, sin punto final.
- **Título de cada gráfico:** describe qué se mide, por ejemplo "Contribution margin by stage". La conclusión ya está en el título de la página.
- **Rótulo:** arriba a la derecha, siempre en el mismo lugar.
- **Mayúsculas:** solo la primera palabra y los nombres propios. No escribir títulos enteros en mayúsculas.

### Estructura de cada página

De arriba hacia abajo:

1. Título, bajada y rótulo.
2. Lo más importante: recomendación, textos clave o tarjetas.
3. Gráfico o tabla principal, a lo ancho.
4. Gráficos de apoyo, de a dos, lado a lado.
5. Notas al pie.

Mantener el título y el rótulo en la misma posición en las 6 páginas. Alinear los bordes de los bloques a la grilla.

### Gráficos

- **Etapas:** en **Style**, usar **Color by > Dimension values** y asignar el color de cada etapa.
- **Variantes:** A siempre `#0F766E` y B siempre `#EA580C`.
- **Una sola serie sin etapas:** usar `#475569`.
- **Etiquetas:** mostrar el valor sobre las columnas cuando haya 6 o menos. Si cada columna tiene su valor, se puede ocultar el eje.
- **Leyenda:** ocultarla si hay una sola serie.
- **Grilla:** dejar solo líneas horizontales finas, con `#E2E8F0`.
- **Evitar:** sombras, degradados, efectos 3D y gráficos de torta.

### Tablas y tarjetas

- **Tablas:** encabezado `#F1F5F9`, sin números de fila y con valores alineados a la derecha.
- **Columna clave:** en negrita, por ejemplo la contribución en la página 1.
- **Formato de números:** moneda ARS sin decimales en tablas, y compacta en tarjetas y ejes (1.8M). Porcentajes con un decimal.
- **Tarjetas:** fondo blanco, borde `#E2E8F0`, valor en 28 px y etiqueta en 12 px.
- **Bloque de recomendación:** fondo `#F0FDFA`, borde `#0F766E`, texto de 16 px.

## Cómo completar el panel Setup

Cada gráfico de abajo sigue el orden del panel **Setup** de Looker Studio. Si un campo no aparece en la lista, dejalo vacío.

| Campo de Looker | Qué va ahí |
|---|---|
| **Data source** | La vista de BigQuery |
| **Dimension** | Cómo se agrupan los datos: etapa, canal, variante o fecha |
| **Breakdown dimension** | Una segunda agrupación dentro de cada barra o columna |
| **Metric** | El número que se muestra |
| **Filter** | Qué filas se excluyen. Se crea con **Add a filter > Include** |
| **Sort** | El orden de las filas o columnas |

**Reglas generales**

- **Stage label y Reason label** son los campos calculados de la sección "Valores de los datos en inglés". Hay que crearlos antes de armar los gráficos.
- **Agregación:** en cada métrica, Looker muestra un selector al lado del nombre. Usar **SUM** en cantidades y dinero, y **AVG** en tasas ya calculadas. Con una fila por categoría, AVG muestra el valor tal cual.
- **Números como dimensión:** `installments` y `horizon_days` son números que funcionan como categorías. Arrastralos desde la lista de campos hasta **Dimension**, aunque Looker los marque como métrica.
- **Tablas:** en la pestaña **Style**, apagar **Show summary row** para que no aparezca la fila de totales.

## Página 1: Executive summary

**Título:** "Keep 6 installments: 12 installments sell 10.6% more but earn 35% less"

**Mensaje:** quien tenga 30 segundos debe irse con la decisión y su impacto en pesos.

**Orden en la página:** recomendación arriba a lo ancho, tabla de KPIs debajo, y los dos gráficos lado a lado al final.

**1. Text**
- **Contenido:** "Recommendation: keep 6 installments. Offering 12 would give up about ARS 1.8M per 3-day event (95% CI: -0.4M to +4.0M)."
- **Debe mostrar:** la decisión, antes que cualquier dato.

**2. Table**
- **Data source:** `vw_ab_summary`
- **Dimension:** `checkout_variant`
- **Metric:** `conversion`, `ticket`, `sales_per_1000_sessions`, `contribution_after_ads_per_1000_sessions` (AVG en las cuatro)
- **Sort:** `checkout_variant`, ascendente
- **Debe mostrar:** B gana en venta, pero pierde en la última columna.

**3. Time series chart**
- **Data source:** `vw_funnel_daily`
- **Dimension:** `date`
- **Metric:** `net_sales` (SUM)
- **Sort:** `date`, ascendente
- **Debe mostrar:** los dos picos de venta en la temporada.

**4. Column chart**
- **Data source:** `vw_profitability_by_stage`
- **Dimension:** Stage label
- **Metric:** `contribution_margin` (AVG)
- **Sort:** Stage label, ascendente
- **Debe mostrar:** el margen cae a la mitad justo en esos picos, de 26% a 12%.

## Página 2: Installments A/B test

**Título:** "B needs +12.4% conversion to break even, and it reached +3.2%"

**Mensaje:** B vende más, pero no alcanza el punto de equilibrio. Es la página que prueba el método, así que muestra también la incertidumbre.

**Orden en la página:** los tres textos en una fila arriba, la tabla de resultados en el centro, y debajo el gráfico por evento junto a la tabla de contribución.

**1. Text**
- **Contenido:** "Conversion lift: observed +3.2%, upper CI +8.6%, break-even +12.4%"
- **Debe mostrar:** el equilibrio queda fuera del intervalo.

**2. Text**
- **Contenido:** "Statistical power: 19% for +3%, 99% for +12.4%"
- **Debe mostrar:** el test alcanza para el efecto que decide.

**3. Text**
- **Contenido:** "With returns refunded: A 26,920, B -5,023"
- **Debe mostrar:** B pierde plata si se reembolsan las devoluciones. No esconder este escenario.

**4. Table**
- **Data source:** `ab_results`
- **Dimension:** `metric`
- **Metric:** `variant_a`, `variant_b`, `diff_b_minus_a`, `ci_low`, `ci_high`, `p_value` (AVG en las seis)
- **Debe mostrar:** qué diferencias son significativas y cuáles no.
- **Nota:** las filas mezclan unidades: la conversión es una proporción y el resto son pesos. Si los decimales se ven mal, excluir `conversion` con un filtro y mostrarla en una tabla aparte, con formato de porcentaje.

**5. Table**
- **Data source:** `ab_results`
- **Dimension:** `metric`
- **Metric:** `diff_b_minus_a`, `ci_low`, `ci_high` (AVG en las tres)
- **Filter:** Include `metric` Equal to `contribution_after_ads_per_1000_sessions`
- **Debe mostrar:** el intervalo de -73,687 a +7,004, sin ocultar que incluye el cero.
- **Nota:** Looker Studio no trae barras de error nativas, por eso va en una tabla.

**6. Column chart**
- **Data source:** `vw_ab_by_event`
- **Dimension:** `event`
- **Breakdown dimension:** `checkout_variant`
- **Metric:** `contribution_after_ads_per_1000_sessions` (AVG)
- **Debe mostrar:** B queda abajo en los dos eventos.

## Página 3: Promotions and profitability

**Título:** "Events double traffic but cut contribution margin by more than half"

**Mensaje:** el costo de las promos explica por qué más venta no significa más plata.

**Orden en la página:** las dos tarjetas de ROI arriba, el combinado a lo ancho, y debajo el mix de cuotas junto a su tabla. El gráfico contra baseline va al final.

**1. Scorecard: Cyber Monday**
- **Data source:** `vw_promo_roi`
- **Metric:** `promo_roi` (AVG)
- **Filter:** Include `event` Equal to `cyber_monday`
- **Debe mostrar:** ROI de -14%.

**2. Scorecard: Black Friday**
- **Data source:** `vw_promo_roi`
- **Metric:** `promo_roi` (AVG)
- **Filter:** Include `event` Equal to `black_friday`
- **Debe mostrar:** ROI de -14%.

**3. Combo chart**
- **Data source:** `vw_profitability_by_stage`
- **Dimension:** Stage label
- **Metric:** `discount_rate` y `contribution_margin` (AVG en las dos). En **Style**, poner la primera como barras y la segunda como línea.
- **Sort:** Stage label, ascendente
- **Debe mostrar:** cuando sube el descuento, baja el margen.

**4. 100% stacked bar chart**
- **Data source:** `vw_ab_installment_mix`
- **Dimension:** `checkout_variant`
- **Breakdown dimension:** `installments`
- **Metric:** `orders` (SUM)
- **Debe mostrar:** B mueve pedidos hacia 12 cuotas, las más caras.

**5. Table**
- **Data source:** `vw_ab_installment_mix`
- **Dimension:** `checkout_variant`, `installments`
- **Metric:** `orders` y `net_sales` y `financing_cost` (SUM); `share_orders` y `financing_rate` (AVG)
- **Sort:** `checkout_variant`, ascendente. Secondary sort: `installments`, ascendente
- **Debe mostrar:** cuánto cuesta cada plan de cuotas.

**6. Column chart**
- **Data source:** `vw_promo_roi`
- **Dimension:** `event`
- **Metric:** `contribution_after_ads`, `baseline_same_weekdays` (SUM en las dos)
- **Debe mostrar:** el evento deja menos que días comunes equivalentes.

## Página 4: Funnel, acquisition and customers

**Título:** "Search returns 3.6x and social 2.4x, but neither recovers its CAC within 4 months"

**Mensaje:** el negocio depende del canal: los canales pagos venden, pero en 4 meses no recuperan lo que cuesta traer a cada cliente.

**Orden en la página:** las 4 tarjetas del embudo arriba, la tabla de canales en el centro, y debajo LTV contra CAC junto al mapa de calor. Nuevos y recurrentes va al final.

**1 a 4. Scorecard, una tarjeta por métrica**
- **Data source:** `vw_funnel_daily`
- **Metric:** `sessions`, `add_to_cart_sessions`, `checkout_sessions`, `orders_funnel` (SUM en todas, una en cada tarjeta)
- **Debe mostrar:** cuánta gente queda en cada paso.

**5. Table**
- **Data source:** `vw_acquisition_by_channel`
- **Dimension:** `channel`
- **Metric:** `ad_spend` (SUM); `ctr`, `cpc`, `cac`, `roas_booked`, `roas_realized` (AVG)
- **Sort:** `ad_spend`, descendente
- **Debe mostrar:** qué rinde cada canal, con ROAS facturado y realizado.

**6. Bar chart**
- **Data source:** `vw_ltv_cac_by_channel`
- **Dimension:** `channel`
- **Metric:** `ltv_observed`, `cac` (AVG en las dos)
- **Filter:** Include `ad_spend` Greater than 0
- **Debe mostrar:** el CAC supera al LTV observado en los canales pagos.

**7. Pivot table with heatmap**
- **Data source:** `vw_cohort_retention`
- **Row dimension:** `cohort_month`
- **Column dimension:** `horizon_days`
- **Metric:** `retention_rate` (AVG)
- **Filter:** Include `eligible_customers` Greater than or equal to 1000
- **Sort:** `cohort_month` y `horizon_days`, ascendente
- **Debe mostrar:** cuántos clientes vuelven a 30, 60 y 90 días.

**8. Stacked column chart**
- **Data source:** `vw_new_vs_returning`
- **Dimension:** Stage label
- **Breakdown dimension:** `customer_type`
- **Metric:** `orders` (SUM)
- **Sort:** Stage label, ascendente
- **Debe mostrar:** los eventos traen sobre todo clientes nuevos.

Nota al pie: "LTV observed over 4 months at most: treat it as a floor." Los canales sin gasto no tienen CAC ni LTV/CAC.

## Página 5: Operations

**Título:** "Late deliveries grow 2.6x during events"

**Mensaje:** el pico de los eventos tensiona la operación, y eso también es un costo de la promoción.

**Orden en la página:** entregas tarde a lo ancho arriba, la tabla debajo, y al final quiebres de stock junto a contactos.

**1. Column chart**
- **Data source:** `vw_ops_by_stage`
- **Dimension:** Stage label
- **Metric:** `late_rate` (AVG)
- **Sort:** Stage label, ascendente
- **Debe mostrar:** salto de ~11% a ~29% en eventos.

**2. Table**
- **Data source:** `vw_ops_by_stage`
- **Dimension:** Stage label
- **Metric:** `p50_delivery_days`, `p90_delivery_days`, `cancel_rate`, `return_rate`, `contacts_per_order`, `csat` (AVG en todas)
- **Sort:** Stage label, ascendente
- **Debe mostrar:** el resto de la operación, etapa por etapa.

**3. Column chart**
- **Data source:** `vw_stockouts_by_stage`
- **Dimension:** Stage label
- **Metric:** campo calculado Stockout rate: `SUM(out_of_stock_days) / SUM(product_days)`
- **Sort:** Stage label, ascendente
- **Debe mostrar:** los quiebres se duplican en eventos.

**4. 100% stacked column chart**
- **Data source:** `vw_contacts_by_reason`
- **Dimension:** Stage label
- **Breakdown dimension:** Reason label
- **Metric:** `contacts` (SUM)
- **Sort:** Stage label, ascendente
- **Debe mostrar:** por qué escriben los clientes en cada etapa.

Nota al pie: "The data does not record sales lost to stockouts."

## Página 6: Data quality and definitions

**Título:** "12 of 13 checks pass, and the one that fails is explained"

**Mensaje:** los números son confiables, y sus límites están a la vista.

**Orden en la página:** la reconciliación arriba, y debajo las definiciones junto a los supuestos.

**1. Table**
- **Data source:** `vw_dq_reconciliation`
- **Dimension:** `check_name`, `severity`, `passed`
- **Metric:** `expected`, `actual` (SUM en las dos)
- **Debe mostrar:** qué chequeos pasan y cuál no.

**2. Text**
- **Contenido:** las métricas clave de `METRICS.md`, traducidas al inglés: conversion, ticket, contribution y ROAS, con su fórmula.
- **Debe mostrar:** cómo se calcula cada número.

**3. Text**
- **Contenido:** supuestos del generador y limitación de stock de `DATA_QUALITY.md`, traducidos al inglés.
- **Debe mostrar:** qué es simulado y qué falla.

## Antes de publicar

- [ ] Conversión A 4.67% y B 4.82% en la página 2.
- [ ] Contribución por 1.000 sesiones: A 95,028 y B 61,719.
- [ ] `net_sales` de `vw_funnel_daily`, sin filtros: 2,808,863,355.17 en total.
- [ ] Filtros aplicados sin romper las tasas: cambiar de filtro y revisar que los valores sigan dentro de lo esperado.
- [ ] Ninguna tabla de tasas muestra una fila de totales.
- [ ] Título, rótulo y colores de A y B iguales en las 6 páginas.
- [ ] Rótulo "Simulated data. Fictional store." en las 6 páginas.
- [ ] Ninguna etapa, motivo o métrica visible en español.
- [ ] Capturas en `docs/screenshots/`.
