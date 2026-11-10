# Modelo y medidas de Power BI

Datos simulados. Las medidas se escribieron contra el modelo de abajo, pero **todavía no se ejecutaron en Power BI**. Usar la tabla "Valores de control" para validarlas.

El archivo `.pbix` se arma a mano en Power BI Desktop.

## Modelo en estrella

**Hechos:** `orders`, `daily_traffic`, `order_items`.
**Dimensiones:** `calendar` (desde `vw_dim_calendar`), `customers`, `products`, `dim_channel`, `dim_variant`.

| Desde (1) | Hacia (N) | Columna |
|---|---|---|
| `calendar` | `orders` | `date` → `order_date` |
| `calendar` | `daily_traffic` | `date` → `date` |
| `dim_channel` | `orders` | `channel` |
| `dim_channel` | `daily_traffic` | `channel` |
| `dim_variant` | `orders` | `checkout_variant` |
| `dim_variant` | `daily_traffic` | `checkout_variant` |
| `customers` | `orders` | `customer_id` |
| `orders` | `order_items` | `order_id` |
| `products` | `order_items` | `product_id` |

Todas las relaciones filtran en una dirección.

`dim_channel` y `dim_variant` son necesarias aunque el brief no las nombra. Sin ellas, un filtro de canal afecta a una sola tabla de hechos y la conversión deja de tener sentido.

```dax
dim_channel = DISTINCT ( UNION ( VALUES ( orders[channel] ), VALUES ( daily_traffic[channel] ) ) )

dim_variant = DISTINCT ( UNION ( VALUES ( orders[checkout_variant] ), VALUES ( daily_traffic[checkout_variant] ) ) )
```

Ocultar `orders[channel]`, `orders[checkout_variant]` y las mismas columnas de `daily_traffic`. Usar siempre las de las dimensiones.

## Columnas calculadas en `orders`

```dax
Contribution =
IF (
    orders[status] = "cancelled",
    0,
    orders[net_sales] - orders[cogs] - orders[payment_fee] - orders[financing_cost]
        - ( orders[shipping_cost] - orders[shipping_charged] )
)

Contribution Refunded =
SWITCH (
    orders[status],
    "cancelled", 0,
    "returned", - ( orders[shipping_cost] + orders[payment_fee] ),
    orders[Contribution]
)
```

## Medidas base

```dax
Sessions = SUM ( daily_traffic[sessions] )
Ad Spend = SUM ( daily_traffic[ad_spend] )
Funnel Orders = SUM ( daily_traffic[orders_funnel] )
Orders = COUNTROWS ( orders )
Orders Not Cancelled = CALCULATE ( [Orders], orders[status] <> "cancelled" )
Net Sales = CALCULATE ( SUM ( orders[net_sales] ), orders[status] <> "cancelled" )
GMV = CALCULATE ( SUM ( orders[gross_sales] ), orders[status] <> "cancelled" )
Discounts = CALCULATE ( SUM ( orders[discount_amount] ), orders[status] <> "cancelled" )
Financing Cost = CALCULATE ( SUM ( orders[financing_cost] ), orders[status] <> "cancelled" )
Contribution Total = SUM ( orders[Contribution] )
Contribution Refunded Total = SUM ( orders[Contribution Refunded] )
```

## Test A/B

Filtrar `calendar[is_event] = TRUE` a nivel de página.

```dax
Conversion = DIVIDE ( [Funnel Orders], [Sessions] )
Ticket = DIVIDE ( [Net Sales], [Orders Not Cancelled] )
Sales per 1000 Sessions = DIVIDE ( [Net Sales], [Sessions] ) * 1000
Contribution after Ads per 1000 =
    DIVIDE ( [Contribution Total] - [Ad Spend], [Sessions] ) * 1000
Contribution Refunded after Ads per 1000 =
    DIVIDE ( [Contribution Refunded Total] - [Ad Spend], [Sessions] ) * 1000
Financing Rate = DIVIDE ( [Financing Cost], [Net Sales] )

Contribution per 1000 A =
    CALCULATE ( [Contribution after Ads per 1000], dim_variant[checkout_variant] = "A" )
Contribution per 1000 B =
    CALCULATE ( [Contribution after Ads per 1000], dim_variant[checkout_variant] = "B" )
Contribution B vs A % =
    DIVIDE ( [Contribution per 1000 B] - [Contribution per 1000 A], [Contribution per 1000 A] )
```

Los intervalos y p-valores no se calculan en DAX: importar `outputs/ab_results_long.csv`.

## Embudo y adquisición

```dax
Bounce Rate = DIVIDE ( SUM ( daily_traffic[bounced_sessions] ), [Sessions] )
Add to Cart Rate = DIVIDE ( SUM ( daily_traffic[add_to_cart_sessions] ), [Sessions] )
Cart Abandonment = 1 - DIVIDE ( [Funnel Orders], SUM ( daily_traffic[add_to_cart_sessions] ) )
CTR = DIVIDE ( SUM ( daily_traffic[clicks] ), SUM ( daily_traffic[impressions] ) )
CPC = DIVIDE ( [Ad Spend], SUM ( daily_traffic[clicks] ) )
ROAS Booked = DIVIDE ( SUM ( orders[net_sales] ), [Ad Spend] )
ROAS Realized =
    DIVIDE ( CALCULATE ( SUM ( orders[net_sales] ), orders[status] = "delivered" ), [Ad Spend] )
Revenue per Visit = DIVIDE ( [Net Sales], [Sessions] )
```

## Rentabilidad

Estas medidas replican los valores de control, que usan solo pedidos entregados.

```dax
Delivered Net Sales = CALCULATE ( SUM ( orders[net_sales] ), orders[status] = "delivered" )
Delivered COGS = CALCULATE ( SUM ( orders[cogs] ), orders[status] = "delivered" )
Discount Rate =
    DIVIDE (
        CALCULATE ( SUM ( orders[discount_amount] ), orders[status] = "delivered" ),
        CALCULATE ( SUM ( orders[gross_sales] ), orders[status] = "delivered" )
    )
Gross Margin = DIVIDE ( [Delivered Net Sales] - [Delivered COGS], [Delivered Net Sales] )
Contribution Margin =
    DIVIDE ( CALCULATE ( SUM ( orders[Contribution] ), orders[status] = "delivered" ), [Delivered Net Sales] )
```

## Clientes y operaciones

```dax
Customers with Orders = DISTINCTCOUNT ( orders[customer_id] )
Repurchase Rate =
    DIVIDE (
        COUNTROWS ( FILTER ( VALUES ( orders[customer_id] ), CALCULATE ( COUNTROWS ( orders ) ) >= 2 ) ),
        [Customers with Orders]
    )
Late Rate = DIVIDE ( SUM ( orders[is_late] ), [Orders Not Cancelled] )
On Time Rate = 1 - [Late Rate]
Cancel Rate = DIVIDE ( CALCULATE ( [Orders], orders[status] = "cancelled" ), [Orders] )
Return Rate = DIVIDE ( CALCULATE ( [Orders], orders[status] = "returned" ), [Orders] )
CSAT = AVERAGE ( orders[csat_score] )
```

Para retención, RFM, LTV y percentiles de entrega, importar las vistas `vw_cohort_retention`, `vw_customer_rfm`, `vw_ltv_cac_by_channel` y `vw_ops_by_stage`.

## Valores de control

| Medida | Filtro | Valor esperado |
|---|---|---|
| Conversion | Eventos, A | 4,67% |
| Conversion | Eventos, B | 4,82% |
| Ticket | Eventos, A | 67.729 |
| Ticket | Eventos, B | 72.987 |
| Sales per 1000 Sessions | Eventos, B | 3.307.443 |
| Contribution after Ads per 1000 | Eventos, A | 95.028 |
| Contribution after Ads per 1000 | Eventos, B | 61.719 |
| Contribution Refunded after Ads per 1000 | Eventos, A | 26.920 |
| Contribution Refunded after Ads per 1000 | Eventos, B | -5.023 |
| Repurchase Rate | Sin filtro | 18,1% |
| ROAS Booked | paid_search | 3,64 |
| ROAS Booked | social_ads | 2,43 |

## Opcional: seguridad por canal

Rol de ejemplo para mostrar row-level security, aplicado sobre `dim_channel`:

```dax
[channel] IN { "paid_search", "social_ads" }
```

Probarlo con "Ver como rol": el rol debería ver solo canales pagos en ambas tablas de hechos.
