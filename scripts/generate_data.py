"""
Generador de datos SIMULADOS para una tienda online ficticia.
Temporada sep-dic 2025, con Cyber Monday (3-5 nov) y Black Friday (28-30 nov).

TODOS LOS DATOS SON SIMULADOS. No representan a ninguna empresa real.
Semilla fija: la misma corrida produce siempre los mismos archivos.
Montos en pesos argentinos simulados.

Uso:  python generate_data.py [carpeta_salida]
"""
import os
import sys

import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)
OUT = sys.argv[1] if len(sys.argv) > 1 else "data"
os.makedirs(OUT, exist_ok=True)

DAYS = pd.date_range("2025-09-01", "2025-12-31", freq="D")
CM = (pd.Timestamp("2025-11-03"), pd.Timestamp("2025-11-05"))
BF = (pd.Timestamp("2025-11-28"), pd.Timestamp("2025-11-30"))


def event_of(d):
    if CM[0] <= d <= CM[1]:
        return "cyber_monday"
    if BF[0] <= d <= BF[1]:
        return "black_friday"
    return "normal"


def stage_of(d):
    if d < CM[0]:
        return "1_pre_evento"
    if d <= CM[1]:
        return "2_cyber_monday"
    if d < BF[0]:
        return "3_entre_eventos"
    if d <= BF[1]:
        return "4_black_friday"
    return "5_post_evento"


# ---------------------------------------------------------------- productos
CATS = {  # categoria: (precio base, margen min, margen max, tasa de devolucion)
    "indumentaria": (18000, 0.45, 0.60, 0.12),
    "calzado": (45000, 0.35, 0.50, 0.14),
    "electro": (120000, 0.15, 0.28, 0.04),
    "hogar": (35000, 0.30, 0.50, 0.05),
    "belleza": (15000, 0.50, 0.65, 0.03),
    "deportes": (40000, 0.30, 0.45, 0.06),
}
rows, pid = [], 1
for cat, (base, mmin, mmax, ret) in CATS.items():
    for _ in range(10):
        price = round(base * rng.lognormal(0, 0.35), -2)
        margin = rng.uniform(mmin, mmax)
        rows.append((pid, f"{cat}_{pid:02d}", cat, price, round(price * (1 - margin), 2), ret))
        pid += 1
products = pd.DataFrame(
    rows, columns=["product_id", "product_name", "category", "list_price", "unit_cost", "return_rate"]
)
pop = rng.pareto(1.5, len(products)) + 1
pop = pop / pop.sum()
P_LIST = products["list_price"].to_numpy()
P_COST = products["unit_cost"].to_numpy()
P_RET = products["return_rate"].to_numpy()
P_CAT = products["category"].to_numpy()

# ------------------------------------------------------------------ trafico
CH = {  # canal: (sesiones base/dia, p carrito, p checkout|carrito, costo por clic, ctr)
    "organic": (2600, 0.12, 0.45, 0, None),
    "paid_search": (1800, 0.11, 0.45, 650, 0.020),
    "social_ads": (1500, 0.08, 0.38, 600, 0.012),
    "email": (700, 0.22, 0.50, 0, None),
    "direct": (900, 0.14, 0.50, 0, None),
}
P_ORDER = 0.60  # probabilidad de comprar una vez en el checkout
WEEK = [1.00, 1.00, 1.00, 1.05, 1.10, 1.15, 1.10]  # lunes a domingo

traffic = []
for i, d in enumerate(DAYS):
    ev = event_of(d)
    t_mult = 2.2 if ev == "cyber_monday" else 2.0 if ev == "black_friday" else 1.0
    growth = 1 + 0.15 * i / len(DAYS)
    for ch, (base, p_atc, p_chk, cpc, ctr) in CH.items():
        mean = base * WEEK[d.dayofweek] * growth * t_mult * rng.normal(1, 0.04)
        s = int(rng.poisson(max(mean, 1)))
        # A/B del checkout solo en eventos: A = hasta 6 cuotas, B = hasta 12 cuotas
        if ev != "normal":
            sa = int(rng.binomial(s, 0.5))
            splits = [("A", sa), ("B", s - sa)]
        else:
            splits = [("A", s)]
        for var, sv in splits:
            atc = int(rng.binomial(sv, min(p_atc * (1.1 if ev != "normal" else 1.0), 0.95)))
            chk = int(rng.binomial(atc, p_chk))
            p_ord = P_ORDER * (1.25 if ev != "normal" else 1.0) * (1.08 if var == "B" else 1.0)
            o = int(rng.binomial(chk, min(p_ord, 0.9)))
            bounced = int(rng.binomial(sv, 0.38 + (0.05 if ch == "social_ads" else 0.0)))
            clicks = sv if cpc else 0
            spend = round(clicks * cpc * rng.normal(1, 0.05) * (1.10 if ev != "normal" else 1.0), 2)
            impressions = int(clicks / ctr) if ctr else 0
            traffic.append(
                (d.date(), ev, stage_of(d), ch, var, sv, bounced, atc, chk, o, impressions, clicks, spend)
            )
traffic = pd.DataFrame(
    traffic,
    columns=[
        "date", "event", "stage", "channel", "checkout_variant", "sessions", "bounced_sessions",
        "add_to_cart_sessions", "checkout_sessions", "orders_funnel",
        "impressions", "clicks", "ad_spend",
    ],
)

# ------------------------------------------------------- clientes y pedidos
PROVINCES = ["Buenos Aires", "CABA", "Cordoba", "Santa Fe", "Mendoza", "Tucuman", "Otras"]
PROV_P = [0.30, 0.22, 0.12, 0.10, 0.07, 0.05, 0.14]
RET_W = {"organic": 1.0, "paid_search": 0.6, "social_ads": 0.3, "email": 2.5, "direct": 1.5}
FIN = {1: 0.0, 3: 0.05, 6: 0.10, 12: 0.20}  # costo de cuotas sin interes que absorbe el comercio
HOURS = np.array([1, 1, 1, 1, 1, 1, 2, 3, 4, 5, 6, 6, 6, 6, 6, 6, 6, 7, 8, 9, 10, 10, 8, 4], dtype=float)
HOURS /= HOURS.sum()

cust_signup_idx, cust_rows = [], []
orders, items, contacts = [], [], []
order_id, contact_id = 1, 1

for i, d in enumerate(DAYS):
    ev = event_of(d)
    day_tr = traffic[traffic["date"] == d.date()]
    chans = np.repeat(day_tr["channel"].to_numpy(), day_tr["orders_funnel"].to_numpy())
    variants = np.repeat(day_tr["checkout_variant"].to_numpy(), day_tr["orders_funnel"].to_numpy())
    perm = rng.permutation(len(chans))
    chans, variants = chans[perm], variants[perm]
    n_orders = len(chans)
    if n_orders == 0:
        continue

    p_ret = (0.10 + 0.15 * i / len(DAYS)) * (0.7 if ev != "normal" else 1.0)
    w_ch = np.array([RET_W[c] for c in chans])
    p_i = np.clip(p_ret * w_ch / w_ch.mean(), 0, 0.9)
    is_ret = (rng.random(n_orders) < p_i) & (len(cust_signup_idx) > 0)

    n_ret = int(is_ret.sum())
    if n_ret:
        age = i - np.array(cust_signup_idx)
        w = np.exp(-age / 45.0) + 0.05
        ret_ids = rng.choice(len(cust_signup_idx), size=n_ret, p=w / w.sum())
    ret_ptr = 0

    for k in range(n_orders):
        ch = chans[k]
        var = variants[k]
        if is_ret[k]:
            cidx = int(ret_ids[ret_ptr])
            ret_ptr += 1
        else:
            cidx = len(cust_signup_idx)
            cust_signup_idx.append(i)
            cust_rows.append(
                (cidx + 1, d.date(), ch, rng.choice(PROVINCES, p=PROV_P))
            )

        n_items = int(np.clip(1 + rng.poisson(0.75 if var == "B" else 0.6), 1, 6))
        pids = rng.choice(len(products), size=n_items, p=pop)
        qtys = 1 + (rng.random(n_items) < 0.15).astype(int)
        gmv = float((P_LIST[pids] * qtys).sum())
        cogs = float((P_COST[pids] * qtys).sum())

        promo = rng.random() < (0.70 if ev != "normal" else 0.12)
        if promo:
            disc_pct = rng.uniform(0.10, 0.30) if ev != "normal" else rng.uniform(0.05, 0.15)
        else:
            disc_pct = 0.0
        discount = round(gmv * disc_pct, 2)
        net_sales = round(gmv - discount, 2)

        if var == "B":
            installments = int(rng.choice([1, 3, 6, 12], p=[0.35, 0.20, 0.30, 0.15]))
        elif ev != "normal":
            installments = int(rng.choice([1, 3, 6], p=[0.40, 0.22, 0.38]))
        else:
            installments = int(rng.choice([1, 3, 6], p=[0.60, 0.20, 0.20]))
        financing_cost = round(net_sales * FIN[installments], 2)
        payment_fee = round(net_sales * 0.03, 2)
        shipping_charged = 0.0 if net_sales >= 60000 else 4500.0
        shipping_cost = round(max(2500.0, rng.normal(5000, 900)) * (1.2 if ev != "normal" else 1.0), 2)

        hour = int(rng.choice(24, p=HOURS))
        ts = pd.Timestamp(d) + pd.Timedelta(hours=hour, minutes=int(rng.integers(0, 60)))

        cancelled = rng.random() < (0.05 if ev != "normal" else 0.03)
        days_real = 1 + rng.gamma(2.2, 1.5 if ev != "normal" else 1.0)
        days_int = int(np.ceil(days_real))
        promised_days = 5
        delivered = not cancelled
        late = delivered and days_int > promised_days
        returned = delivered and (rng.random() < float(P_RET[pids].mean()))
        status = "cancelled" if cancelled else "returned" if returned else "delivered"

        delivered_date = (d + pd.Timedelta(days=days_int)).date() if delivered else None
        csat = None
        if delivered and rng.random() < 0.25:
            pr = [0.25, 0.20, 0.20, 0.20, 0.15] if late else [0.03, 0.04, 0.10, 0.28, 0.55]
            csat = int(rng.choice([1, 2, 3, 4, 5], p=pr))

        orders.append((
            order_id, cidx + 1, ts, d.date(), ev, stage_of(d), ch, var, status,
            int(is_ret[k]), int(promo), round(disc_pct, 4), installments,
            round(gmv, 2), discount, net_sales, round(cogs, 2),
            payment_fee, financing_cost, shipping_charged, shipping_cost,
            (d + pd.Timedelta(days=promised_days)).date(), delivered_date,
            int(late), csat,
        ))
        for pj, q in zip(pids, qtys):
            items.append((order_id, int(pj) + 1, P_CAT[pj], int(q), float(P_LIST[pj]), float(P_COST[pj])))

        p_contact, reason = 0.05, "consulta_general"
        if cancelled:
            p_contact, reason = 0.50, "cancelacion"
        elif returned:
            p_contact, reason = 0.80, "devolucion"
        elif late:
            p_contact, reason = 0.30, "demora_entrega"
        if rng.random() < p_contact:
            contacts.append((contact_id, order_id, (ts + pd.Timedelta(days=int(rng.integers(0, 4)))).date(), reason))
            contact_id += 1
        order_id += 1

orders = pd.DataFrame(orders, columns=[
    "order_id", "customer_id", "order_ts", "order_date", "event", "stage", "channel", "checkout_variant", "status",
    "is_returning_customer", "promo_flag", "discount_pct", "installments",
    "gross_sales", "discount_amount", "net_sales", "cogs",
    "payment_fee", "financing_cost", "shipping_charged", "shipping_cost",
    "promised_delivery_date", "delivered_date", "is_late", "csat_score",
])
order_items = pd.DataFrame(items, columns=[
    "order_id", "product_id", "category", "quantity", "list_price", "unit_cost",
])
customers = pd.DataFrame(cust_rows, columns=["customer_id", "signup_date", "acquisition_channel", "province"])
contacts = pd.DataFrame(contacts, columns=["contact_id", "order_id", "contact_date", "reason"])

# ------------------------------------------------------------------- stock
stock = []
for d in DAYS:
    ev = event_of(d)
    p_out = 0.08 if ev != "normal" else 0.03
    out = rng.random(len(products)) < p_out
    for pj in range(len(products)):
        stock.append((d.date(), pj + 1, int(not out[pj])))
daily_stock = pd.DataFrame(stock, columns=["date", "product_id", "in_stock"])

# --------------------------------------------------------------- exportar
for name, df in {
    "products": products, "daily_traffic": traffic, "customers": customers,
    "orders": orders, "order_items": order_items, "contacts": contacts,
    "daily_stock": daily_stock,
}.items():
    df.to_csv(os.path.join(OUT, f"{name}.csv"), index=False)
    print(f"{name}.csv: {len(df):,} filas")

# ------------------------------------------------- resumen para validar
tot_sess = traffic["sessions"].sum()
print("\n--- RESUMEN (datos simulados) ---")
print(f"Sesiones: {tot_sess:,} | Pedidos: {len(orders):,} | Clientes: {len(customers):,}")
print(f"Conversion global: {len(orders) / tot_sess:.2%}")
ok = orders[orders["status"] == "delivered"]
print(f"Ticket promedio (entregados): {ok['net_sales'].mean():,.0f}")
print(f"Cancelacion: {(orders['status'] == 'cancelled').mean():.1%} | "
      f"Devolucion: {(orders['status'] == 'returned').mean():.1%}")
rep = orders.groupby("customer_id").size()
print(f"Tasa de recompra (2+ pedidos): {(rep >= 2).mean():.1%}")

g = orders[orders["status"] == "delivered"].groupby("stage").agg(
    pedidos=("order_id", "count"), ventas_netas=("net_sales", "sum"),
    cogs=("cogs", "sum"), fee=("payment_fee", "sum"), fin=("financing_cost", "sum"),
    ship=("shipping_cost", "sum"), ship_ch=("shipping_charged", "sum"),
    desc=("discount_amount", "sum"), bruto=("gross_sales", "sum"), tarde=("is_late", "mean"),
)
g["margen_bruto"] = (g.ventas_netas - g.cogs) / g.ventas_netas
g["margen_contrib_pre_ads"] = (g.ventas_netas - g.cogs - g.fee - g.fin - (g.ship - g.ship_ch)) / g.ventas_netas
g["tasa_descuento"] = g.desc / g.bruto
print("\nPor etapa (pedidos entregados):")
print(g[["pedidos", "ventas_netas", "margen_bruto", "margen_contrib_pre_ads", "tasa_descuento", "tarde"]].round(3).to_string())

adv = traffic.groupby("channel").agg(spend=("ad_spend", "sum"), orders=("orders_funnel", "sum"))
rev = orders.groupby("channel")["net_sales"].sum()
adv["roas"] = rev / adv["spend"].replace(0, np.nan)
print("\nROAS por canal pago:")
print(adv[adv["spend"] > 0].round(2).to_string())
print(f"\nContactos por pedido: {len(contacts) / len(orders):.3f}")

# ---------------------------------------------------- resumen test A/B (eventos)
ev_o = orders[(orders["event"] != "normal") & (orders["status"] != "cancelled")].copy()
ev_o["contrib"] = (ev_o.net_sales - ev_o.cogs - ev_o.payment_fee - ev_o.financing_cost
                   - (ev_o.shipping_cost - ev_o.shipping_charged))
ev_t = traffic[traffic["event"] != "normal"].groupby("checkout_variant").agg(
    sesiones=("sessions", "sum"), pedidos=("orders_funnel", "sum"), gasto=("ad_spend", "sum"))
ab = ev_o.groupby("checkout_variant").agg(ticket=("net_sales", "mean"), venta=("net_sales", "sum"),
                                          contrib=("contrib", "sum"))
ab = ev_t.join(ab)
ab["conversion"] = ab.pedidos / ab.sesiones
ab["contrib_menos_ads_por_1000_ses"] = (ab.contrib - ab.gasto) / ab.sesiones * 1000
ab["venta_por_1000_ses"] = ab.venta / ab.sesiones * 1000
print("\nTest A/B en eventos (A=hasta 6 cuotas, B=hasta 12):")
print(ab[["sesiones", "pedidos", "conversion", "ticket", "venta_por_1000_ses", "contrib_menos_ads_por_1000_ses"]].round(4).to_string())
