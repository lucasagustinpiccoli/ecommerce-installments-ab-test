# ¿Le conviene a la tienda ofrecer 12 cuotas sin interés en Cyber Monday y Black Friday?

**Recomendación: mantener 6 cuotas.** Las 12 cuotas venden 10,6% más por sesión, pero dejan menos plata: 33.309 ARS menos de contribución después de publicidad cada 1.000 sesiones (-35%). Eso equivale a resignar unos 1,8 M ARS en un evento de 3 días (IC 95%: de -0,4 M a +4,0 M).

> **Todos los datos de la tienda son simulados** (seed 42). No representan a ninguna empresa real. El efecto de las cuotas sobre la conversión y el ticket es **un supuesto del generador**: este proyecto demuestra el **método** de análisis, no un descubrimiento sobre consumidores reales.

## La decisión

Las cuotas sin interés las financia la tienda: 3 cuotas cuestan alrededor del 5% de la venta neta, 6 cuotas el 10% y 12 cuotas el 20%. La pregunta es si ofrecer hasta 12 cuotas (variante B) en lugar de hasta 6 (variante A) sube la conversión y el ticket lo suficiente para pagar ese costo.

## Resultado del test A/B

El test corrió solo durante los dos eventos, con las sesiones repartidas 50/50.

| | A: hasta 6 cuotas | B: hasta 12 cuotas | Diferencia B - A | ¿Significativa al 95%? |
|---|---|---|---|---|
| Sesiones | 54.905 | 54.948 | | |
| Pedidos | 2.562 | 2.646 | | |
| Conversión | 4,67% | 4,82% | +3,2% (p = 0,245) | No |
| Ticket | 67.729 | 72.987 | +7,8% (p = 0,001) | Sí |
| Venta por 1.000 sesiones | 2,99 M | 3,31 M | +10,6% | Sí |
| Costo de financiación sobre la venta | 5,0% | 7,0% | +1,9 pp | |
| Contribución después de publicidad por 1.000 sesiones | 95.028 | 61.719 | -35,1% | No, por poco |

Con reembolso de devoluciones, la contribución por 1.000 sesiones baja a 26.920 para A y a -5.023 para B: en ese escenario, B pierde plata después de publicidad.

## Por qué la recomendación se sostiene aunque el -35% no sea significativo

El intervalo de la diferencia de contribución va de -73.687 a +7.004 por 1.000 sesiones. Incluye el cero apenas, así que el test no prueba por sí solo que B deje menos. La probabilidad de que B supere a A es de alrededor del 5%. Tres cosas apoyan la decisión:

1. **B necesita mucha más conversión de la que muestra.** Para empatar con A necesita +12,4% de conversión (+14,0% con reembolso de devoluciones). Observó +3,2%, y el techo de su intervalo es +8,6%.
2. **El test sí alcanza para ver ese efecto.** No alcanza para detectar un +3%: harían falta 361.427 sesiones por variante, 6,6 veces lo observado, y su poder actual es del 19%. Pero tiene un poder del 99% para detectar el +12,4% que importa para decidir.
3. **Ambos eventos apuntan igual.** B queda por debajo tanto en Cyber Monday (61.442 contra 82.547) como en Black Friday (61.987 contra 107.134).

Incluso si la mejora real fuera de +8% (el supuesto del generador sobre quienes llegan al checkout), B seguiría abajo: 79.026 contra 95.028.

## Qué haría cambiar la recomendación

- **Bajar el costo de las 12 cuotas:** con la conversión observada, B empata si el costo pasa de 20% a 13,1% de la venta. Es lo primero que negociaría con el banco o la procesadora de pagos.
- **Una mejora de conversión confirmada de al menos +12,4%** en un test nuevo. Se detecta con unas 22.000 sesiones por variante, menos que las de un solo evento.

## Lo que este análisis no responde

- **Efectos después del evento.** Los datos no permiten medir si quien compró en 12 cuotas vuelve más o menos.
- **Devoluciones reales.** La definición base conserva la contribución de los pedidos devueltos. Por eso se muestran los dos escenarios.
- **El costo de oportunidad de los eventos.** Los dos eventos dejan menos contribución que días comunes equivalentes (ROI de promo: -14% en Cyber Monday, -14% en Black Friday), con cualquier variante. Es otra decisión, pero merece su propio análisis.

## Cómo está armado

```
data_raw/   CSV generados (no se versionan; run_all.sh los recrea)
scripts/    generate_data.py, ab_test.py, verify_local.py, load_bigquery.sh
sql/        vistas por bloque, schemas explícitos y orden de ejecución
outputs/    resultados del test y de los chequeos
docs/       README, METRICS, DASHBOARD_SPEC, DATA_QUALITY
powerbi/    modelo en estrella y medidas DAX
```

Stack: Python, SQL, BigQuery, Power BI y Looker Studio.

## Reproducir

```bash
pip install -r requirements.txt
bash run_all.sh
```

`run_all.sh` genera los datos, corre el test, ejecuta las 19 vistas en DuckDB y las compara contra los valores de control. Si encuentra `bq` instalado y autenticado, además carga todo en BigQuery. Sin `bq`, saltea solo ese paso.

Las 19 vistas se ejecutaron en BigQuery (dataset `ecom_sim`) y en DuckDB, con los mismos resultados.

En el sandbox gratuito de BigQuery, las tablas y vistas vencen a los 60 días. Volver a correr `bash scripts/load_bigquery.sh` las recrea.

- [METRICS.md](METRICS.md): definición de cada métrica.
- [DATA_QUALITY.md](DATA_QUALITY.md): reconciliaciones y limitaciones.
- [DASHBOARD_SPEC.md](DASHBOARD_SPEC.md): especificación del dashboard de 6 páginas.
- [measures.md](../powerbi/measures.md): modelo y medidas de Power BI.
