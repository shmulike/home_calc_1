import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

# -------------------- Finance helpers --------------------
def mortgage_monthly_payment(principal, annual_rate, years):
    if principal <= 0:
        return 0.0
    r = annual_rate / 12.0
    n = int(years * 12)
    if r == 0:
        return principal / n
    return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

def amortization_with_extra(principal, annual_rate, years, extra_principal_monthly=0.0, months=None):
    """Return (months_axis, balance_array) with optional constant extra principal per month."""
    if principal <= 0:
        if months is None:
            months = 1
        m_axis = np.arange(months + 1)
        return m_axis, np.zeros_like(m_axis, dtype=float)

    r = annual_rate / 12.0
    n = int(years * 12)
    pay = mortgage_monthly_payment(principal, annual_rate, years)

    if months is None:
        months = n

    bal = principal
    m_axis = [0]
    balances = [bal]

    for k in range(1, months + 1):
        if bal <= 0:
            m_axis.append(k)
            balances.append(0.0)
            continue

        interest = bal * r
        principal_part = pay - interest
        extra = max(0.0, extra_principal_monthly)

        total_principal = max(0.0, principal_part + extra)
        if total_principal > bal:
            total_principal = bal
        bal = bal - total_principal

        m_axis.append(k)
        balances.append(bal)

    return np.array(m_axis), np.array(balances)

def grow_monthly(initial_value, annual_growth, months):
    if months <= 0:
        return np.array([initial_value], dtype=float)
    g = annual_growth / 12.0
    idx = np.arange(months + 1)
    return initial_value * ((1 + g) ** idx)

def future_value_series_monthly(initial_lump, monthly_contrib, annual_return, months):
    """FV series with monthly compounding and monthly contributions."""
    r = annual_return / 12.0
    out = np.zeros(months + 1, dtype=float)
    amt = float(initial_lump)
    out[0] = amt
    for i in range(1, months + 1):
        amt = amt * (1 + r) + monthly_contrib
        out[i] = amt
    return out

# -------------------- App UI --------------------
st.set_page_config(page_title="Real‑Estate Two‑Scenario Simulator", layout="wide")
st.title("Real‑Estate Two‑Scenario Simulator")

with st.sidebar:
    st.subheader("Global")
    horizon_years = st.number_input("Horizon (years)", min_value=2, max_value=50, value=15, step=1)
    prop_growth_pct = st.number_input("Property annual appreciation (%)", min_value=0.0, max_value=20.0, value=3.0, step=0.1)
    prop_growth = prop_growth_pct / 100.0

    st.markdown("---")
    st.subheader("Scenario 1: Keep Apt #1 (rent) + Mortgage on Apt #2")
    v1 = st.number_input("Apt #1 value (ILS)", min_value=0.0, value=1_900_000.0, step=10_000.0, format="%.0f")
    v2 = st.number_input("Apt #2 value (ILS)", min_value=0.0, value=2_300_000.0, step=10_000.0, format="%.0f")

    mort_principal_1 = st.number_input("Mortgage principal (ILS)", min_value=0.0, value=1_700_000.0, step=10_000.0, format="%.0f")
    mort_rate_pct_1  = st.number_input("Mortgage annual rate (%)", min_value=0.0, max_value=30.0, value=4.0, step=0.1)
    mort_rate_1 = mort_rate_pct_1 / 100.0
    mort_years_1 = st.number_input("Mortgage term (years)", min_value=1, max_value=40, value=25, step=1)

    monthly_rent_1 = st.number_input("Monthly rent from Apt #1 (ILS)", min_value=0.0, value=4_500.0, step=100.0, format="%.0f")
    extra_from_rent_1 = st.number_input("Extra principal from rent (ILS/mo)", min_value=0.0, value=4_500.0, step=100.0, format="%.0f")

    monthly_payment = mortgage_monthly_payment(mort_principal_1, mort_rate_1, mort_years_1)
    st.info(f"**Monthly mortgage payment (ILS):** {monthly_payment:,.0f}")

    st.markdown("---")
    st.subheader("Scenario 2: Sell Apt #1, No Mortgage; Invest Difference + Monthly Contribution")
    equity_return_pct_2 = st.number_input("Equity portfolio annual return (%)", min_value=0.0, max_value=50.0, value=6.5, step=0.1)
    equity_return_2 = equity_return_pct_2 / 100.0
    monthly_contrib_2 = st.number_input("Monthly contribution to equity (ILS)", min_value=0.0, value=7_000.0, step=100.0, format="%.0f")

    init_lump_2 = max(0.0, v1 - mort_principal_1)  # as requested (e.g., 1.9M - 1.7M = 200k)
    st.info(f"**Equity initial lump (ILS):** {init_lump_2:,.0f}  (Apt #1 sale − Mortgage principal)")

# -------------------- Computation --------------------
months = horizon_years * 12

# Scenario 1: assets & debt
m_axis_1, bal_1 = amortization_with_extra(
    principal=mort_principal_1,
    annual_rate=mort_rate_1,
    years=mort_years_1,
    extra_principal_monthly=extra_from_rent_1,
    months=months
)
apt1_series = grow_monthly(v1, prop_growth, months)
apt2_series = grow_monthly(v2, prop_growth, months)
assets_1 = apt1_series + apt2_series

# Scenario 2: assets only (no debt)
years_axis = m_axis_1 / 12.0
apt2_series_2 = grow_monthly(v2, prop_growth, months)
equity_series = future_value_series_monthly(init_lump_2, monthly_contrib_2, equity_return_2, months)
assets_2 = apt2_series_2 + equity_series

# Shared Y scale
y_max = max(np.max(assets_1), np.max(bal_1), np.max(assets_2))
y_max = 1.05 * y_max if y_max > 0 else 1.0

# -------------------- Plot --------------------
toM = 1_000_000.0
fig, ax = plt.subplots(figsize=(10, 6))

# Scenario 1
ax.plot(years_axis, assets_1 / toM, label="Scenario 1: Assets", color="tab:blue", linestyle="-")
ax.plot(years_axis, bal_1 / toM,    label="Scenario 1: Debt",   color="tab:blue", linestyle="--")

# Scenario 2
ax.plot(years_axis, assets_2 / toM, label="Scenario 2: Assets", color="tab:orange", linestyle="-")

ax.set_title("Assets and Debt Over Time (Common X, Same Y Scale)")
ax.set_xlabel("Years")
ax.set_ylabel("Million ILS")
ax.set_ylim(0, y_max / toM)
ax.grid(True)
ax.legend()

st.pyplot(fig, clear_figure=True)

st.caption(
    "Scenario 2 starts with an initial equity equal to (Apt #1 sale − Mortgage principal) "
    "and adds a fixed monthly contribution into the equity portfolio."
)
