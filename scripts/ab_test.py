"""
Test A/B de cuotas en eventos: A = hasta 6 cuotas, B = hasta 12 cuotas.
DATOS SIMULADOS. El efecto de las cuotas es un supuesto del generador: esto demuestra
el metodo, no un descubrimiento.

Salidas: outputs/ab_results.json, outputs/ab_results_long.csv, outputs/ab_installment_mix.csv
Falla (exit 1) si los numeros no reproducen los valores de control del brief.

Uso:  python scripts/ab_test.py [carpeta_datos] [carpeta_salida]
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

DATA = sys.argv[1] if len(sys.argv) > 1 else "data_raw"
OUT = sys.argv[2] if len(sys.argv) > 2 else "outputs"
os.makedirs(OUT, exist_ok=True)

SEED = 42
N_BOOT = 10_000
ALPHA = 0.05
POWER = 0.80
TARGET_LIFT = 0.03  # +3% relativo sobre la conversion de A
rng = np.random.default_rng(SEED)


# ------------------------------------------------------------------- datos
orders = pd.read_csv(os.path.join(DATA, "orders.csv"))
traffic = pd.read_csv(os.path.join(DATA, "daily_traffic.csv"))
ev_o = orders[orders["event"] != "normal"].copy()
ev_t = traffic[traffic["event"] != "normal"]

# Definicion del brief: un pedido devuelto conserva su contribucion.
# Es optimista: asume que la venta devuelta no se reembolsa.
ev_o["contrib"] = (ev_o.net_sales - ev_o.cogs - ev_o.payment_fee - ev_o.financing_cost
                   - (ev_o.shipping_cost - ev_o.shipping_charged))
ev_o.loc[ev_o.status == "cancelled", "contrib"] = 0.0
ev_o["sale"] = ev_o.net_sales.where(ev_o.status != "cancelled", 0.0)

# Escenario conservador: se reembolsa la venta y se recupera la mercaderia;
# se pierden el envio y la comision de pago.
ev_o["contrib_returns_refunded"] = ev_o["contrib"]
is_ret = ev_o.status == "returned"
ev_o.loc[is_ret, "contrib_returns_refunded"] = -(ev_o.shipping_cost + ev_o.payment_fee)[is_ret]

SES = ev_t.groupby("checkout_variant")["sessions"].sum()
ADS = ev_t.groupby("checkout_variant")["ad_spend"].sum()
ORD = ev_o.groupby("checkout_variant").size()
A = ev_o[ev_o.checkout_variant == "A"]
B = ev_o[ev_o.checkout_variant == "B"]
A_ok, B_ok = A[A.status != "cancelled"], B[B.status != "cancelled"]


# --------------------------------------------------------- 1. conversion
def prop_test(x1, n1, x2, n2):
    p1, p2 = x1 / n1, x2 / n2
    pooled = (x1 + x2) / (n1 + n2)
    z = (p2 - p1) / np.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    se = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    crit = stats.norm.ppf(1 - ALPHA / 2)
    return p1, p2, z, 2 * stats.norm.sf(abs(z)), p2 - p1 - crit * se, p2 - p1 + crit * se


conv_a, conv_b, conv_z, conv_p, conv_lo, conv_hi = prop_test(ORD.A, SES.A, ORD.B, SES.B)

# ----------------------------------------------------------- 2. ticket
welch = stats.ttest_ind(B_ok.net_sales, A_ok.net_sales, equal_var=False)
tk_ci = welch.confidence_interval(1 - ALPHA)
tk_a, tk_b = A_ok.net_sales.mean(), B_ok.net_sales.mean()


# ------------------------------------------- 3. bootstrap por sesion
def per_session_boot(values, n_sessions):
    """Una sesion aporta 0 si no compro, o el valor de un pedido si compro."""
    conv = len(values) / n_sessions
    counts = rng.binomial(n_sessions, conv, N_BOOT)
    return np.array([rng.choice(values, c, replace=True).sum() / n_sessions for c in counts])


def compare(col, subtract_ads):
    va, vb = A[col].to_numpy(), B[col].to_numpy()
    ad_a = ADS.A / SES.A if subtract_ads else 0.0
    ad_b = ADS.B / SES.B if subtract_ads else 0.0
    point_a = va.sum() / SES.A - ad_a
    point_b = vb.sum() / SES.B - ad_b
    boot_a = per_session_boot(va, SES.A) - ad_a
    boot_b = per_session_boot(vb, SES.B) - ad_b
    diff = boot_b - boot_a
    lo, hi = np.percentile(diff, [2.5, 97.5])
    return {
        "a_per_1000": point_a * 1000, "b_per_1000": point_b * 1000,
        "diff_per_1000": (point_b - point_a) * 1000,
        "diff_lo_per_1000": lo * 1000, "diff_hi_per_1000": hi * 1000,
        "pct_diff": point_b / point_a - 1,
        "prob_b_beats_a": float((diff > 0).mean()),
    }


sales = compare("sale", subtract_ads=False)
contrib = compare("contrib", subtract_ads=True)
contrib_conservative = compare("contrib_returns_refunded", subtract_ads=True)

# ----------------------------------------------------- 4. cuotas: costo y mix
mix = ev_o[ev_o.status != "cancelled"].groupby(["checkout_variant", "installments"]).agg(
    orders=("order_id", "count"), net_sales=("net_sales", "sum"), financing_cost=("financing_cost", "sum"),
).reset_index()
mix["share_orders"] = mix.orders / mix.groupby("checkout_variant").orders.transform("sum")
mix["financing_rate"] = mix.financing_cost / mix.net_sales
mix.to_csv(os.path.join(OUT, "ab_installment_mix.csv"), index=False)
fin_rate_a = A_ok.financing_cost.sum() / A_ok.net_sales.sum()
fin_rate_b = B_ok.financing_cost.sum() / B_ok.net_sales.sum()


# ------------------------------------------------- 5. punto de equilibrio
def breakeven(col):
    """Conversion que necesita B para empatar con A, manteniendo su contribucion por pedido."""
    k_a = A[col].sum() / SES.A - ADS.A / SES.A
    per_order_b = B[col].mean()
    needed = (k_a + ADS.B / SES.B) / per_order_b
    return {"needed_conversion_b": needed, "needed_lift_vs_a": needed / conv_a - 1}


be = breakeven("contrib")
be_cons = breakeven("contrib_returns_refunded")

# Tasa de financiacion de 12 cuotas que hace empatar a B con A, con la conversion observada
b12 = B_ok[B_ok.installments == 12]
gap_pesos = -contrib["diff_per_1000"] / 1000 * SES.B
be_rate_12 = (b12.financing_cost.sum() - gap_pesos) / b12.net_sales.sum()

# Que pasaria si el efecto verdadero de conversion fuera el que tiene el generador en el checkout (+8%)
assumed_lift = 0.08
k_b_assumed = conv_a * (1 + assumed_lift) * B["contrib"].mean() - ADS.B / SES.B
k_a = contrib["a_per_1000"] / 1000
k_b_assumed_cons = conv_a * (1 + assumed_lift) * B["contrib_returns_refunded"].mean() - ADS.B / SES.B
k_a_cons = contrib_conservative["a_per_1000"] / 1000


# ----------------------------------------------------- 6. poder del test
def n_per_arm(p1, lift, alpha=ALPHA, power=POWER):
    p2 = p1 * (1 + lift)
    pbar = (p1 + p2) / 2
    za, zb = stats.norm.ppf(1 - alpha / 2), stats.norm.ppf(power)
    num = za * np.sqrt(2 * pbar * (1 - pbar)) + zb * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    return int(np.ceil((num / (p2 - p1)) ** 2))


def achieved_power(p1, lift, n, alpha=ALPHA):
    p2 = p1 * (1 + lift)
    se = np.sqrt(p1 * (1 - p1) / n + p2 * (1 - p2) / n)
    return float(stats.norm.sf(stats.norm.ppf(1 - alpha / 2) - (p2 - p1) / se))


n_arm = int(min(SES.A, SES.B))
sessions_per_event = float(ev_t.groupby("event")["sessions"].sum().mean())
needed = n_per_arm(conv_a, TARGET_LIFT)
za_zb = stats.norm.ppf(1 - ALPHA / 2) + stats.norm.ppf(POWER)
mde_abs = za_zb * np.sqrt(2 * conv_a * (1 - conv_a) / n_arm)
power = {
    "target_relative_lift": TARGET_LIFT,
    "sessions_needed_per_arm": needed,
    "sessions_observed_per_arm": n_arm,
    "times_observed_sample": needed / n_arm,
    "equivalent_events_of_3_days": needed * 2 / sessions_per_event,
    "achieved_power_at_target": achieved_power(conv_a, TARGET_LIFT, n_arm),
    "mde_relative_at_80_power": mde_abs / conv_a,
    "sessions_needed_per_arm_for_breakeven": n_per_arm(conv_a, be["needed_lift_vs_a"]),
    "achieved_power_at_breakeven": achieved_power(conv_a, be["needed_lift_vs_a"], n_arm),
}

# -------------------------------------------------- 7. impacto por evento
impact = {
    "sessions_per_event": sessions_per_event,
    "a_minus_b_per_event": -contrib["diff_per_1000"] / 1000 * sessions_per_event,
    "lo": -contrib["diff_hi_per_1000"] / 1000 * sessions_per_event,
    "hi": -contrib["diff_lo_per_1000"] / 1000 * sessions_per_event,
    "a_minus_b_per_event_returns_refunded": -contrib_conservative["diff_per_1000"] / 1000 * sessions_per_event,
}

# ---------------------------------------------------------- por evento
by_event = {}
for ev, g in ev_o.groupby("event"):
    t = ev_t[ev_t.event == ev].groupby("checkout_variant").agg(s=("sessions", "sum"), a=("ad_spend", "sum"))
    c = g.groupby("checkout_variant").contrib.sum()
    k = (c - t.a) / t.s * 1000
    by_event[ev] = {"a_per_1000": k.A, "b_per_1000": k.B}

# ----------------------------------------------------------- resultados
results = {
    "note": "DATOS SIMULADOS. El efecto de las cuotas es un supuesto del generador.",
    "seed": SEED, "n_boot": N_BOOT,
    "sessions": {"A": int(SES.A), "B": int(SES.B)},
    "orders": {"A": int(ORD.A), "B": int(ORD.B)},
    "conversion": {"a": conv_a, "b": conv_b, "relative_lift": conv_b / conv_a - 1, "z": conv_z,
                   "p_value": conv_p, "diff_ci": [conv_lo, conv_hi]},
    "ticket": {"a": tk_a, "b": tk_b, "relative_lift": tk_b / tk_a - 1, "welch_t": float(welch.statistic),
               "p_value": float(welch.pvalue), "diff_ci": [float(tk_ci.low), float(tk_ci.high)]},
    "sales_per_1000_sessions": sales,
    "contribution_after_ads_per_1000_sessions": contrib,
    "contribution_after_ads_returns_refunded": contrib_conservative,
    "financing_rate": {"a": fin_rate_a, "b": fin_rate_b},
    "breakeven": {
        "brief_definition": be,
        "returns_refunded": be_cons,
        "observed_lift": conv_b / conv_a - 1,
        "conversion_lift_ci_upper": conv_hi / conv_a,
        "financing_rate_12_to_tie": float(be_rate_12),
    },
    "if_true_conversion_lift_8pct": {
        "b_per_1000": k_b_assumed * 1000, "a_per_1000": k_a * 1000,
        "b_per_1000_returns_refunded": k_b_assumed_cons * 1000, "a_per_1000_returns_refunded": k_a_cons * 1000,
    },
    "power": power,
    "impact_per_3_day_event": impact,
    "by_event": by_event,
}
with open(os.path.join(OUT, "ab_results.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=float)

rows = [
    ("conversion", conv_a, conv_b, conv_b - conv_a, conv_lo, conv_hi, conv_p),
    ("ticket", tk_a, tk_b, tk_b - tk_a, float(tk_ci.low), float(tk_ci.high), float(welch.pvalue)),
]
for name, r in [("sales_per_1000_sessions", sales), ("contribution_after_ads_per_1000_sessions", contrib),
                ("contribution_after_ads_returns_refunded", contrib_conservative)]:
    rows.append((name, r["a_per_1000"], r["b_per_1000"], r["diff_per_1000"],
                 r["diff_lo_per_1000"], r["diff_hi_per_1000"], None))
pd.DataFrame(rows, columns=["metric", "variant_a", "variant_b", "diff_b_minus_a", "ci_low", "ci_high", "p_value"]
             ).to_csv(os.path.join(OUT, "ab_results_long.csv"), index=False)

# --------------------------------------------------------------- consola
print("Test A/B en eventos (DATOS SIMULADOS)")
print(f"Conversion  A {conv_a:.2%} | B {conv_b:.2%} | z={conv_z:.2f} p={conv_p:.3f}")
print(f"Ticket      A {tk_a:,.0f} | B {tk_b:,.0f} | t={welch.statistic:.2f} p={welch.pvalue:.4f}")
print(f"Venta/1000  A {sales['a_per_1000']:,.0f} | B {sales['b_per_1000']:,.0f} | {sales['pct_diff']:+.1%} "
      f"IC95 dif [{sales['diff_lo_per_1000']:,.0f}; {sales['diff_hi_per_1000']:,.0f}]")
print(f"Contrib-ads/1000 A {contrib['a_per_1000']:,.0f} | B {contrib['b_per_1000']:,.0f} | {contrib['pct_diff']:+.1%} "
      f"IC95 dif [{contrib['diff_lo_per_1000']:,.0f}; {contrib['diff_hi_per_1000']:,.0f}] "
      f"P(B>A)={contrib['prob_b_beats_a']:.3f}")
print(f"  con reembolso de devoluciones: A {contrib_conservative['a_per_1000']:,.0f} | "
      f"B {contrib_conservative['b_per_1000']:,.0f} "
      f"IC95 dif [{contrib_conservative['diff_lo_per_1000']:,.0f}; {contrib_conservative['diff_hi_per_1000']:,.0f}] "
      f"P(B>A)={contrib_conservative['prob_b_beats_a']:.3f}")
print(f"Equilibrio: B necesita {be['needed_lift_vs_a']:+.1%} de conversion vs A "
      f"(observado {conv_b / conv_a - 1:+.1%}); con reembolso {be_cons['needed_lift_vs_a']:+.1%}")
print(f"Tasa de 12 cuotas para empatar: {be_rate_12:.1%} (hoy 20%)")
print(f"Si el lift real fuera +8%: B {k_b_assumed * 1000:,.0f} vs A {k_a * 1000:,.0f}; "
      f"con reembolso B {k_b_assumed_cons * 1000:,.0f} vs A {k_a_cons * 1000:,.0f}")
print(f"Poder: {needed:,} sesiones por brazo para +3% ({needed / n_arm:.1f}x lo observado, "
      f"{power['equivalent_events_of_3_days']:.0f} eventos); poder actual {power['achieved_power_at_target']:.0%}, "
      f"MDE {power['mde_relative_at_80_power']:.1%}; poder para el equilibrio "
      f"{power['achieved_power_at_breakeven']:.0%} ({power['sessions_needed_per_arm_for_breakeven']:,} por brazo)")
print(f"Impacto por evento de 3 dias (A - B): {impact['a_minus_b_per_event']:,.0f} ARS "
      f"[{impact['lo']:,.0f}; {impact['hi']:,.0f}]")

# ------------------------------------------- control contra el brief
CONTROL = [  # nombre, valor, esperado, tolerancia absoluta
    ("sesiones A", SES.A, 54905, 0), ("sesiones B", SES.B, 54948, 0),
    ("pedidos A", ORD.A, 2562, 0), ("pedidos B", ORD.B, 2646, 0),
    ("conversion A %", conv_a * 100, 4.67, 0.005), ("conversion B %", conv_b * 100, 4.82, 0.005),
    ("ticket A", tk_a, 67729, 1), ("ticket B", tk_b, 72987, 1),
    ("venta/1000 A M", sales["a_per_1000"] / 1e6, 2.99, 0.005),
    ("venta/1000 B M", sales["b_per_1000"] / 1e6, 3.31, 0.005),
    ("contrib/1000 A", contrib["a_per_1000"], 95028, 1), ("contrib/1000 B", contrib["b_per_1000"], 61719, 1),
    ("z conversion", conv_z, 1.16, 0.01), ("p conversion", conv_p, 0.25, 0.01),
    ("z ticket", welch.statistic, 3.2, 0.05),
]
bad = [(n, float(v), e) for n, v, e, tol in CONTROL if abs(v - e) > tol]
if bad:
    print("\nAVISO: no reproduce el control del brief:")
    for n, v, e in bad:
        print(f"  {n}: obtenido {v:.4f}, esperado {e}")
    sys.exit(1)
print(f"\nControl OK: {len(CONTROL)} valores reproducen el brief.")
