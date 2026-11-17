"""
Analisis de sensibilidad: ¿con que supuestos convendria ofrecer 12 cuotas (B) en lugar de 6 (A)?
DATOS SIMULADOS. El efecto de las cuotas es un supuesto del generador; este script no cambia
el generador ni el test. Solo recalcula la contribucion de B variando tres supuestos:

  (a) aumento de conversion de B frente a A (0% a 20%)
  (b) costo de financiacion de las 12 cuotas, % de la venta (5% a 25%; se agrega 32,29% como
      referencia: la tabla publica de Mercado Pago, ver docs/ASSUMPTIONS.md)
  (c) aumento de ticket de B frente a A (0% a 20%)

Modelo (misma definicion de contribucion que ab_test.py: devoluciones conservan la contribucion,
cancelados aportan 0, se resta publicidad):

  contribucion B por sesion = conv_A x (1 + a) x c_B(b, c) - publicidad B por sesion
  c_B = s x [T_A x (1 + c) x (1 - cogs - comision - financiacion(b))  -  envio neto]

donde s = share de pedidos B no cancelados, cogs, comision y envio neto salen de los pedidos B
observados, y financiacion(b) es la tasa de B con su mix de cuotas observado y la tasa de 12
cuotas reemplazada por b. Simplificaciones: el mix de cuotas, el costo de mercaderia en % y el
envio neto por pedido no cambian con el ticket.
Control: con los valores observados el modelo reproduce el resultado del test (falla si no).

Salidas: outputs/sensitivity_grid.csv, outputs/sensitivity_breakeven.csv,
         docs/report/sensitivity.png

Uso:  python scripts/sensitivity.py [carpeta_datos] [carpeta_salida]
"""
import json
import os
import sys

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

DATA = sys.argv[1] if len(sys.argv) > 1 else "data_raw"
OUT = sys.argv[2] if len(sys.argv) > 2 else "outputs"
FIG = os.path.join("docs", "report", "sensitivity.png")
MP_12 = 0.3229  # Mercado Pago, costo por ofrecer 12 cuotas (ver docs/ASSUMPTIONS.md)

orders = pd.read_csv(os.path.join(DATA, "orders.csv"))
traffic = pd.read_csv(os.path.join(DATA, "daily_traffic.csv"))
ev_o = orders[orders["event"] != "normal"].copy()
ev_t = traffic[traffic["event"] != "normal"]
ses = ev_t.groupby("checkout_variant")["sessions"].sum()
ads = ev_t.groupby("checkout_variant")["ad_spend"].sum()

ev_o["contrib"] = (ev_o.net_sales - ev_o.cogs - ev_o.payment_fee - ev_o.financing_cost
                   - (ev_o.shipping_cost - ev_o.shipping_charged))
ev_o.loc[ev_o.status == "cancelled", "contrib"] = 0.0

A = ev_o[ev_o.checkout_variant == "A"]
B = ev_o[ev_o.checkout_variant == "B"]
A_ok, B_ok = A[A.status != "cancelled"], B[B.status != "cancelled"]

conv_a = len(A) / ses.A
conv_b_obs = len(B) / ses.B
tk_a = A_ok.net_sales.mean()
tk_b_obs = B_ok.net_sales.mean()
a_per_session = A.contrib.sum() / ses.A - ads.A / ses.A

ns = B_ok.net_sales.sum()
s_ok = len(B_ok) / len(B)
cogs_r = B_ok.cogs.sum() / ns
fee_r = B_ok.payment_fee.sum() / ns
fin_other = B_ok.loc[B_ok.installments != 12, "financing_cost"].sum() / ns
share_12 = B_ok.loc[B_ok.installments == 12, "net_sales"].sum() / ns
ship_net = (B_ok.shipping_cost - B_ok.shipping_charged).mean()
ads_b = ads.B / ses.B
fin12_obs = B_ok.loc[B_ok.installments == 12, "financing_cost"].sum() / \
    B_ok.loc[B_ok.installments == 12, "net_sales"].sum()


def b_minus_a(conv_lift, fin12, ticket_lift):
    """Contribucion despues de publicidad cada 1.000 sesiones: B - A (positivo = conviene B)."""
    fin = fin_other + share_12 * fin12
    c_b = s_ok * (tk_a * (1 + ticket_lift) * (1 - cogs_r - fee_r - fin) - ship_net)
    b = conv_a * (1 + conv_lift) * c_b - ads_b
    return (b - a_per_session) * 1000


def needed_lift(fin12, ticket_lift):
    """Aumento de conversion que necesita B para empatar con A."""
    fin = fin_other + share_12 * fin12
    c_b = s_ok * (tk_a * (1 + ticket_lift) * (1 - cogs_r - fee_r - fin) - ship_net)
    return (a_per_session + ads_b) / (conv_a * c_b) - 1


# ---------------------------------------------------------------- control
obs = dict(conv_lift=conv_b_obs / conv_a - 1, fin12=fin12_obs, ticket_lift=tk_b_obs / tk_a - 1)
res = json.load(open(os.path.join(OUT, "ab_results.json"), encoding="utf-8"))
c = res["contribution_after_ads_per_1000_sessions"]
expected = c["b_per_1000"] - c["a_per_1000"]
got = b_minus_a(**obs)
if abs(got - expected) > 1e-6 * abs(expected):
    sys.exit(f"El modelo no reproduce el test: {got:,.2f} contra {expected:,.2f}")
be_obs = needed_lift(fin12_obs, obs["ticket_lift"])
if abs(be_obs - res["breakeven"]["brief_definition"]["needed_lift_vs_a"]) > 1e-9:
    sys.exit("El modelo no reproduce el punto de equilibrio de ab_test.py")
print(f"Control OK: B - A observado = {got:,.0f} por 1.000 sesiones; equilibrio {be_obs:+.1%}")
print(f"Observado: conversion {obs['conv_lift']:+.1%}, ticket {obs['ticket_lift']:+.1%}, "
      f"12 cuotas {fin12_obs:.0%}, {share_12:.1%} de la venta de B en 12 cuotas")

# ------------------------------------------------------------- grillas
lifts = np.round(np.arange(0, 0.2001, 0.01), 2)
fins = np.round(np.arange(0.05, 0.2501, 0.01), 2)
tickets = np.round(np.arange(0, 0.2001, 0.01), 2)
rows = []
for cl in lifts:
    for f in fins:
        rows.append(("conv_x_fin12", cl, f, obs["ticket_lift"], b_minus_a(cl, f, obs["ticket_lift"])))
    for t in tickets:
        rows.append(("conv_x_ticket", cl, fin12_obs, t, b_minus_a(cl, fin12_obs, t)))
grid = pd.DataFrame(rows, columns=["grid", "conv_lift", "fin12", "ticket_lift", "b_minus_a_per_1000"])
grid["better"] = np.where(grid.b_minus_a_per_1000 > 0, "B (12 cuotas)", "A (6 cuotas)")
grid.to_csv(os.path.join(OUT, "sensitivity_grid.csv"), index=False)

be_fins = [0.05, 0.10, 0.131, 0.15, 0.20, 0.25, MP_12]
be_tks = [0.0, 0.04, round(obs["ticket_lift"], 3), 0.12, 0.16, 0.20]
be = pd.DataFrame([[needed_lift(f, t) for t in be_tks] for f in be_fins],
                  index=[f"{f:.1%}" for f in be_fins], columns=[f"ticket {t:+.1%}" for t in be_tks])
be.index.name = "costo 12 cuotas"
be.to_csv(os.path.join(OUT, "sensitivity_breakeven.csv"))
print("\nAumento de conversion que necesita B para empatar con A:")
print(be.map(lambda v: f"{v:+.1%}").to_string())

# ------------------------------------------------------------- grafico
SLATE, ORANGE = "#475569", "#EA580C"
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
panels = [
    (axes[0], np.linspace(0.05, 0.35, 121), "Costo de financiación de 12 cuotas (% de la venta)",
     lambda x, y: b_minus_a(y, x, obs["ticket_lift"]), obs["fin12"],
     f"Ticket de B fijo en {obs['ticket_lift']:+.1%} (observado)"),
    (axes[1], np.linspace(0.0, 0.20, 121), "Aumento de ticket de B",
     lambda x, y: b_minus_a(y, fin12_obs, x), obs["ticket_lift"],
     f"Costo de 12 cuotas fijo en {fin12_obs:.0%} (supuesto del generador)"),
]
ys = np.linspace(0, 0.20, 121)
for ax, xs, xlabel, f, x_obs, subtitle in panels:
    X, Y = np.meshgrid(xs, ys)
    Z = np.vectorize(f)(X, Y)
    ax.contourf(X, Y, Z, levels=[Z.min() - 1, 0, Z.max() + 1], colors=["#E2E8F0", "#FED7AA"])
    cs = ax.contour(X, Y, Z, levels=[0], colors=["#0F172A"], linewidths=1.6)
    ax.clabel(cs, fmt={0: "empate"}, fontsize=8)
    ax.scatter([x_obs], [obs["conv_lift"]], color="#0F172A", zorder=5)
    ax.annotate("observado", (x_obs, obs["conv_lift"]), textcoords="offset points", xytext=(6, -12), fontsize=8)
    ax.axhline(res["breakeven"]["conversion_lift_ci_upper"], color=SLATE, ls=":", lw=1)
    ax.text(xs[0], res["breakeven"]["conversion_lift_ci_upper"] + 0.003, "techo del IC 95% (+8,6%)",
            fontsize=7, color=SLATE)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Aumento de conversión de B")
    ax.set_title(subtitle, fontsize=9, color=SLATE)
    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.05 if ax is axes[0] else 0.04))
    ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.04))
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
# Zona B (naranja): arriba a la izquierda en el panel 1 (12 cuotas baratas), arriba a la derecha en el 2
axes[0].text(0.03, 0.95, "conviene 12 cuotas", transform=axes[0].transAxes, ha="left", va="top",
             color=ORANGE, fontsize=10, fontweight="bold")
axes[0].text(0.97, 0.05, "conviene 6 cuotas", transform=axes[0].transAxes, ha="right", va="bottom",
             color=SLATE, fontsize=10, fontweight="bold")
axes[1].text(0.97, 0.95, "conviene 12 cuotas", transform=axes[1].transAxes, ha="right", va="top",
             color=ORANGE, fontsize=10, fontweight="bold")
axes[1].text(0.03, 0.05, "conviene 6 cuotas", transform=axes[1].transAxes, ha="left", va="bottom",
             color=SLATE, fontsize=10, fontweight="bold")
axes[0].axvline(0.25, color=SLATE, ls="--", lw=0.8)
axes[0].axvline(MP_12, color=ORANGE, ls="--", lw=0.8)
axes[0].text(MP_12, 0.125, "Mercado Pago\n32,29% ", fontsize=7, color=ORANGE, ha="right")
axes[0].text(0.25, 0.125, "fin del rango\npedido (25%) ", fontsize=7, color=SLATE, ha="right")
fig.suptitle("¿Cuándo conviene ofrecer 12 cuotas? Contribución después de publicidad, B contra A "
             "(datos simulados)", fontsize=11)
os.makedirs(os.path.dirname(FIG), exist_ok=True)
fig.savefig(FIG, dpi=150)
print(f"\nGrafico: {FIG}")
