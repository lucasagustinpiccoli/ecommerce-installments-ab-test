# Guía para defender el tablero

Resumen página por página: qué quiere demostrar cada página, qué significa cada métrica y por qué está ahí. Al final, preguntas probables con su respuesta.

## De dónde salen los datos

**Todos los datos son simulados.** No vienen de ninguna empresa real.

1. **Generación:** `scripts/generate_data.py` crea una tienda online ficticia con semilla fija (seed 42), así que siempre da los mismos datos. Produce 7 tablas en CSV: productos, clientes, tráfico diario, pedidos, ítems de pedido, contactos a soporte y stock diario. Cubre una temporada de septiembre a diciembre, con Cyber Monday y Black Friday en el medio.
2. **El test A/B:** durante los dos eventos, las sesiones se reparten 50/50 entre la variante A (hasta 6 cuotas sin interés) y la B (hasta 12). `scripts/ab_test.py` calcula diferencias, intervalos de confianza, p-valores, punto de equilibrio y poder estadístico. El resultado queda en la tabla `ab_results`.
3. **BigQuery:** `scripts/load_bigquery.sh` carga las tablas en el dataset `ecom_sim` y crea 19 vistas SQL (`sql/`). Cada vista resume los datos para un gráfico.
4. **Data Studio:** el tablero se conecta a esas vistas. No hace cálculos propios, salvo traducir etapas y motivos al inglés y la tasa de quiebre de stock.
5. **Control:** `scripts/verify_local.py` corre las mismas vistas en DuckDB y las compara contra 22 valores de control. Coinciden.

**Lo que esto significa al defenderlo:** el efecto de las cuotas sobre la conversión y el ticket es un supuesto del generador. El proyecto demuestra el **método** para tomar la decisión, no un descubrimiento sobre compradores reales.

## La pregunta del proyecto

¿Le conviene a la tienda ofrecer 12 cuotas sin interés en Cyber Monday y Black Friday, en lugar de 6?

Las cuotas sin interés las paga la tienda. Cuestan alrededor del 5% de la venta con 3 cuotas, 10% con 6 y 20% con 12. Ofrecer 12 cuotas solo conviene si sube la conversión o el ticket lo suficiente para pagar ese costo extra.

**Respuesta:** mantener 6 cuotas.

---

## Página 1: Executive summary

**Qué quiere demostrar:** la decisión y su impacto en pesos, para alguien que tiene 30 segundos.

| Elemento | Qué muestra | Por qué está |
|---|---|---|
| Título | B vende 10,6% más pero gana 35% menos | Resume la tensión central: más venta no es más plata |
| Recomendación | Mantener 6 cuotas. Ofrecer 12 resigna unos ARS 1,8 M por evento de 3 días (IC 95%: -0,4 M a +4,0 M) | Traduce el resultado a una cifra de negocio, con su incertidumbre |
| Tabla de KPIs por variante | Conversión, ticket, venta y contribución cada 1.000 sesiones | Pone lado a lado lo que B gana y lo que B pierde |
| Ventas netas por día | La serie de toda la temporada, con dos picos | Muestra que los eventos son los días de mayor venta |
| Margen de contribución por etapa | 26% en días normales, ~12% en eventos | Muestra que en los picos de venta el margen cae a la mitad |

**Métricas:**
- **Conversión:** pedidos / sesiones. De cada 100 visitas, cuántas compran.
- **Ticket (Avg. order value):** venta neta promedio por pedido, sin cancelados.
- **Venta por 1.000 sesiones:** venta neta / sesiones × 1.000. Combina conversión y ticket en un solo número. Se mide por sesiones y no por pedidos porque las dos variantes tuvieron el mismo tráfico: así se compara qué hace cada una con la misma cantidad de visitas.
- **Contribución después de publicidad por 1.000 sesiones:** lo que queda después de restar costo de mercadería, comisión de pago, costo de financiación de las cuotas, envío y publicidad. **Es la métrica de decisión**, porque mide plata y no volumen.
- **Margen de contribución:** contribución / venta neta, antes de publicidad.

---

## Página 2: Installments A/B test

**Qué quiere demostrar:** que la conclusión tiene respaldo estadístico, y mostrar la incertidumbre en lugar de esconderla. Es la página del método.

| Elemento | Qué muestra | Por qué está |
|---|---|---|
| Título | B necesita +12,4% de conversión para empatar y logró +3,2% | Es el argumento más fuerte de la decisión |
| Texto 1 | Mejora observada +3,2%, techo del intervalo +8,6%, equilibrio +12,4% | Aun en el mejor caso plausible, B no llega al equilibrio |
| Texto 2 | Poder del 19% para detectar +3%, 99% para detectar +12,4% | El test no alcanza para ver efectos chicos, pero sí el efecto que decide |
| Texto 3 | Con devoluciones reembolsadas: A 26.920, B -5.023 | En el escenario pesimista, B pierde plata |
| Tabla de resultados | Ticket, venta y contribución por variante, con diferencia, IC 95% y p-valor | Qué diferencias son significativas y cuáles no |
| Tabla de conversión | 4,67% contra 4,82%, p = 0,245 | Separada porque es una proporción y el resto son pesos |
| Gráfico por evento | Contribución cada 1.000 sesiones en Black Friday y Cyber Monday | B queda abajo en los dos eventos, no solo en el promedio |
| Tabla de contribución | Diferencia -33.309, IC de -73.687 a +7.004 | Data Studio no tiene barras de error; la tabla muestra el intervalo |

**Métricas:**
- **Diferencia B - A:** cuánto más (o menos) logra B.
- **Intervalo de confianza 95% (CI low / CI high):** el rango donde probablemente está la diferencia real. Si incluye el cero, la diferencia no es significativa.
- **p-valor:** probabilidad de ver una diferencia así si en realidad no hubiera ninguna. Por debajo de 0,05 se considera significativa. Ticket: p = 0,001 (significativo). Conversión: p = 0,245 (no significativo).
- **Punto de equilibrio:** cuánta conversión extra necesita B para igualar la contribución de A, pagando el costo de las 12 cuotas. Da +12,4%.
- **Poder estadístico:** probabilidad de que el test detecte un efecto si existe. Bajo para +3% (19%), muy alto para +12,4% (99%).

**Cómo se lee el conjunto:** la diferencia de contribución (-35%) no es significativa por sí sola, porque su intervalo roza el cero. La decisión se sostiene por tres razones: B necesita +12,4% y ni el techo del intervalo (+8,6%) llega; el test tiene poder de sobra para detectar ese +12,4%; y B pierde en los dos eventos por separado.

---

## Página 3: Promotions and profitability

**Qué quiere demostrar:** por qué vender más en un evento no significa ganar más. Explica de dónde sale la pérdida de margen.

| Elemento | Qué muestra | Por qué está |
|---|---|---|
| ROI de promo | Cyber Monday -14,5%, Black Friday -13,6% | Los eventos, con cualquier variante, dejan menos que días comunes equivalentes |
| Descuento contra margen por etapa | Barras de descuento y línea de margen | Cuando sube el descuento, el margen cae de 26% a ~12% |
| Mix de cuotas por variante | Porcentaje de pedidos en 1, 3, 6 y 12 cuotas | B mueve pedidos hacia 12 cuotas, las más caras para la tienda |
| Tabla por plan de cuotas | Pedidos, venta, costo de financiación, participación y tasa | Muestra el costo real de cada plan. En B, 364 pedidos (14,6%) usan 12 cuotas, con 20% de costo |
| Evento contra línea base | Contribución después de publicidad en días de evento contra días comunes equivalentes | Black Friday 4,7 M contra 10,2 M; Cyber Monday 3,9 M contra 9,1 M |

**Métricas:**
- **Tasa de descuento:** descuentos / GMV (venta bruta).
- **Margen de contribución:** contribución / venta neta, antes de publicidad.
- **Costo de financiación:** lo que la tienda le paga al banco o procesadora por ofrecer cuotas sin interés.
- **Tasa de financiación:** costo de financiación / venta neta del plan.
- **ROI de promo:** (contribución del evento - línea base) / (descuentos + financiación). Negativo significa que la promoción costó más de lo que aportó.
- **Línea base (same weekdays):** contribución promedio de días comunes del mismo día de la semana, antes y después del evento. Se ajusta por día de semana para no comparar un viernes con un martes.

**Aclaración para defender:** el ROI negativo de los eventos es otra decisión distinta de las cuotas. Queda a la vista porque es relevante, pero no cambia la recomendación del test.

---

## Página 4: Funnel, acquisition and customers

**Qué quiere demostrar:** el contexto del negocio más allá del test. Los canales pagos venden, pero en 4 meses no recuperan lo que cuesta traer a cada cliente.

| Elemento | Qué muestra | Por qué está |
|---|---|---|
| Tarjetas del embudo | 1.094.662 sesiones → 134.522 con carrito → 61.384 en checkout → 37.861 pedidos | Dónde se pierde la gente en el camino a comprar |
| Tabla de canales | Inversión, CTR, CPC, CAC, ROAS facturado y realizado | Qué rinde cada canal |
| LTV contra CAC | Search: 19.164 contra 23.395. Social: 19.293 contra 33.046 | En los dos canales pagos, el cliente cuesta más de lo que dejó hasta ahora |
| Mapa de calor de retención | Cohortes por mes, recompra a 30, 60 y 90 días | Cuántos clientes vuelven a comprar |
| Nuevos y recurrentes por etapa | Pedidos por tipo de cliente | Los eventos traen sobre todo clientes nuevos |

**Métricas:**
- **CTR:** clics / impresiones de anuncios.
- **CPC:** inversión / clics. Cuánto cuesta cada clic.
- **CAC:** inversión / clientes nuevos del canal. Cuánto cuesta conseguir un cliente.
- **ROAS facturado:** venta de todos los pedidos / inversión. Search 3,6x, social 2,4x.
- **ROAS realizado:** venta de pedidos entregados y no devueltos / inversión. Search 3,2x, social 2,2x. Es el que importa, porque descuenta lo que no se cobró.
- **LTV observado:** contribución que dejó cada cliente desde que llegó. Cubre como máximo 4 meses, así que es un **piso**, no el valor de toda la vida del cliente.
- **Retención 30/60/90:** clientes que vuelven a comprar dentro de esos días / clientes que tuvieron esos días para hacerlo. Solo se muestran cohortes con 1.000 clientes o más, para no sacar conclusiones de grupos chicos.

**Aclaración para defender:** un ROAS de 3,6x parece bueno, pero el ROAS mide venta y no margen. Por eso se compara LTV contra CAC: muestra si el cliente devuelve lo que costó. Con 4 meses de historia, todavía no.

---

## Página 5: Operations

**Qué quiere demostrar:** el pico de los eventos tensiona la operación, y eso también es un costo de la promoción.

| Elemento | Qué muestra | Por qué está |
|---|---|---|
| Entregas tarde por etapa | ~11% en días normales, 28,6% en Cyber Monday y 30,5% en Black Friday | Es el titular: las entregas tarde se multiplican por 2,6 |
| Tabla de operación | CSAT, contactos por pedido, entrega P50 y P90, cancelación y devolución | El resto de la operación, etapa por etapa |
| Quiebres de stock | ~3% en días normales, ~7,5% en eventos | La falta de stock se duplica en eventos |
| Motivos de contacto | Porcentaje de cada motivo por etapa | En eventos crecen los reclamos por entrega tarde |

**Métricas:**
- **Tasa de entregas tarde:** pedidos entregados tarde / pedidos no cancelados.
- **P50 y P90 de entrega:** días hasta la entrega para la mitad de los pedidos (P50) y para el 90% (P90). El P90 muestra la cola de pedidos más demorados.
- **Contactos por pedido:** contactos a soporte / pedidos.
- **CSAT:** satisfacción promedio (1 a 5). Responde ~25% de los clientes entregados. En Black Friday baja a 3,90.
- **Tasa de quiebre de stock:** producto-días sin stock / producto-días totales.

**Aclaración para defender:** los datos no registran las ventas perdidas por falta de stock, así que no se puede estimar cuánto se dejó de vender. Por eso la nota al pie.

---

## Página 6: Data quality and definitions

**Qué quiere demostrar:** que los números son confiables y que sus límites están a la vista.

| Elemento | Qué muestra | Por qué está |
|---|---|---|
| Tabla de chequeos | 13 controles con valor esperado y obtenido | 12 pasan. El que falla aparece primero y está explicado |
| Definiciones | Fórmula de conversión, ticket, contribución y ROAS | Cualquiera puede verificar cómo se calcula cada número |
| Supuestos y límites | Datos simulados, efecto de las cuotas supuesto, limitación de stock | Lo que el análisis no puede afirmar |

**El chequeo que falla:** 1.809 líneas de pedido (2,97%) se vendieron con el producto marcado sin stock, porque el generador crea el stock por separado de los pedidos. Se midió su efecto: sin esos pedidos, A queda en 57.293 y B en 16.571 por cada 1.000 sesiones. La conclusión no cambia. No se corrigieron los datos para no alterar lo validado: se dejó la limitación visible.

**Regla de cálculo:** toda tasa se calcula como SUM(numerador) / SUM(denominador). Promediar tasas ya calculadas da un resultado incorrecto.

---

## Preguntas probables

**¿Por qué no alcanza con mirar la conversión?**
Porque la conversión subió (+3,2%) y aun así B gana menos. Las cuotas tienen un costo que la conversión no muestra. La métrica de decisión tiene que medir plata.

**Si la diferencia de contribución no es significativa, ¿cómo podés recomendar algo?**
Porque la pregunta no es si B es distinto, sino si B llega a cubrir su costo. Para eso necesita +12,4% de conversión, y ni el techo del intervalo (+8,6%) llega. Además el test tenía 99% de poder para detectar ese +12,4%, y B pierde en los dos eventos por separado.

**¿Por qué medir cada 1.000 sesiones y no por pedido?**
Porque las dos variantes recibieron el mismo tráfico. Medir por sesión captura a la vez cuántos compran y cuánto gastan. Medir por pedido ignoraría la diferencia de conversión.

**¿Qué haría cambiar la recomendación?**
Que baje el costo de las 12 cuotas: B empata si pasa de 20% a 13,1% de la venta. O un test nuevo que confirme al menos +12,4% de conversión, que se detecta con unas 22.000 sesiones por variante.

**¿Por qué mostrar el escenario con devoluciones reembolsadas?**
Porque la definición base conserva la contribución de los pedidos devueltos, lo que es optimista. Con reembolso, B pierde plata. Mostrar los dos escenarios evita elegir el que más conviene.

**¿Los datos son reales?**
No. Son simulados, y lo aclara cada página. El proyecto demuestra cómo se toma la decisión: diseño del test, métrica correcta, incertidumbre y límites.
