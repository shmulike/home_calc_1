import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# =========================
# DISPLAY / STYLE SETTINGS
# =========================
graph_col_width       = 7   # left column width (graph). Right column gets the rest (out of 10)
plot_width            = 9   # matplotlib figure width
plot_height           = 4   # matplotlib figure height
legend_fontsize       = 8   # legend font size
axis_label_fontsize   = 8   # axis labels & title font size
axis_tick_fontsize    = 8   # axis tick numbers font size

st.set_page_config(page_title="Keep vs Sell: Apartment vs Stocks", layout="wide")
st.title("Keep the Apartment & Pay Mortgage vs Sell and Invest")

# =========================
# LAYOUT: Graph (left) | Inputs (right)
# =========================
col_graph, col_inputs = st.columns([graph_col_width, 10 - graph_col_width])

with col_inputs:
    # ---------------------
    # General (2-per-row; second column left as spacer)
    # ---------------------
    st.header("General")
    g1, g2 = st.columns(2)
    with g1:
        years_projection = st.number_input(
            "Projection Years",
            min_value=1, value=20, step=1, key="years_projection"
        )
    with g2:
        st.empty()  # spacer to keep two-per-row layout

    years_projection = int(years_projection)

    # ---------------------
    # Property Parameters
    # ---------------------
    st.header("Property Parameters")
    p1, p2 = st.columns(2)
    with p1:
        apt_value = st.number_input(
            "Apartment Value (ILS)",
            min_value=0.0, value=1_900_000.0, step=10_000.0, format="%.0f", key="apt_value"
        )
    with p2:
        re_growth_pct = st.number_input(
            "Annual Real Estate Growth (%)",
            min_value=0.0, value=3.00, step=0.10, format="%.2f", key="re_growth_pct"
        )

    p3, p4 = st.columns(2)
    with p3:
        monthly_rent = st.number_input(
            "Monthly Rent income (ILS)",
            min_value=0.0, value=4_000.0, step=100.0, format="%.0f", key="monthly_rent"
        )
    with p4:
        st.empty()  # spacer

    # ---------------------
    # Mortgage Parameters
    # ---------------------
    st.header("Mortgage Parameters")
    m1, m2 = st.columns(2)
    with m1:
        mortgage_amount = st.number_input(
            "Mortgage Amount (ILS)",
            min_value=0.0, value=1_700_000.0, step=10_000.0, format="%.0f", key="mortgage_amount"
        )
    with m2:
        mortgage_years = st.number_input(
            "Mortgage Years",
            min_value=1, value=15, step=1, key="mortgage_years"
        )
    mortgage_years = int(mortgage_years)

    m3, m4 = st.columns(2)
    with m3:
        mortgage_rate_pct = st.number_input(
            "Mortgage Annual Rate (%)",
            min_value=0.0, value=5.50, step=0.10, format="%.2f", key="mortgage_rate_pct"
        )
    with m4:
        st.empty()  # spacer

    # >>> Mortgage calculation shown here (right after Mortgage inputs) <<<
    n_pay = mortgage_years * 12
    r_m = (mortgage_rate_pct / 100.0) / 12.0
    if mortgage_amount > 0 and n_pay > 0:
        if r_m > 0:
            mortgage_payment = mortgage_amount * (r_m * (1 + r_m) ** n_pay) / ((1 + r_m) ** n_pay - 1)
        else:
            mortgage_payment = mortgage_amount / n_pay
    else:
        mortgage_payment = 0.0

    net_monthly_after_rent = mortgage_payment - monthly_rent

    st.info(
        f"**Monthly Mortgage Payment:** {mortgage_payment:,.0f} ₪   ‎\n<br>"
        f"**Net Monthly (payment − rent):** {net_monthly_after_rent:,.0f} ₪"
    )

    # ---------------------
    # Stock Market
    # ---------------------
    st.header("Stock Market")
    s1, s2 = st.columns(2)
    with s1:
        initial_deposit = st.number_input(
            "Initial deposit (ILS)",
            min_value=0.0, value=200_000.0, step=10_000.0, format="%.0f", key="initial_deposit"
        )
    with s2:
        monthly_deposit = st.number_input(
            "Monthly Deposit (ILS)",
            min_value=0.0, value=6_000.0, step=100.0, format="%.0f", key="monthly_deposit"
        )

    s3, s4 = st.columns(2)
    with s3:
        stock_return_pct = st.number_input(
            "Annual Stock Market Return (%)",
            min_value=0.0, value=7.00, step=0.10, format="%.2f", key="stock_return_pct"
        )
    with s4:
        st.empty()  # spacer

# =========================
# CALCULATIONS (vectorized so the lines always span full horizon)
# =========================
months = years_projection * 12
idx_m = np.arange(months + 1)           # 0..months
years_axis = idx_m / 12.0

re_growth = re_growth_pct / 100.0
stock_return = stock_return_pct / 100.0

# --- Scenario 1: Apartment value over time (monthly compounding) ---
apt_series_s1 = apt_value * (1.0 + re_growth / 12.0) ** idx_m  # shape (months+1,)

# --- Scenario 1: Mortgage remaining balance series ---
def mortgage_balance_series(P, annual_rate_pct, years_term, months_horizon):
    """Vectorized remaining balance B_k for k=0..months_horizon."""
    n = int(years_term) * 12
    r = (annual_rate_pct / 100.0) / 12.0
    k = np.arange(months_horizon + 1)

    if P <= 0 or n <= 0:
        return np.zeros_like(k, dtype=float)

    m = np.minimum(k, n)
    if r == 0:
        # Linear paydown to zero by month n, then stay at 0
        B = P * (1 - m / n)
        B[k > n] = 0.0
        return B

    # Payment
    M = P * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    # Remaining balance formula
    B = P * (1 + r) ** m - M * (((1 + r) ** m - 1) / r)
    B[k > n] = 0.0
    # Numerical cleanup
    B = np.maximum(0.0, B)
    return B

debt_series_s1 = mortgage_balance_series(mortgage_amount, mortgage_rate_pct, mortgage_years, months)

# --- Scenario 2: Equity portfolio series ---
def equity_series(initial_lump, monthly_contrib, annual_return_pct, months_horizon):
    """FV series: initial*(1+r)^k + contrib*(( (1+r)^k -1)/r ), vectorized for k=0..months."""
    r = (annual_return_pct / 100.0) / 12.0
    k = np.arange(months_horizon + 1)
    if r == 0:
        return initial_lump + monthly_contrib * k
    growth = (1 + r) ** k
    return initial_lump * growth + monthly_contrib * (growth - 1) / r

equity_series_s2 = equity_series(initial_deposit, monthly_deposit, stock_return_pct, months)

# Shared Y max (in ILS) — ensure full-range plotting
y_max = max(np.max(apt_series_s1), np.max(debt_series_s1), np.max(equity_series_s2))
y_max = 1.05 * y_max if y_max > 0 else 1.0

# =========================
# PLOT
# =========================
with col_graph:
    fig, ax = plt.subplots(figsize=(plot_width, plot_height))

    # Scenario 1 (Apartment & Debt)
    ax.plot(years_axis, apt_series_s1 / 1_000_000.0, label="Scenario 1: Apartment Value", color="tab:blue", linestyle="-")
    ax.plot(years_axis, debt_series_s1 / 1_000_000.0, label="Scenario 1: Mortgage Debt", color="tab:blue", linestyle="--")

    # Scenario 2 (Equity Portfolio only)
    ax.plot(years_axis, equity_series_s2 / 1_000_000.0, label="Scenario 2: Equity Portfolio", color="tab:orange", linestyle="-")

    ax.set_title("Keep & Pay Mortgage vs Sell & Invest — Over Time", fontsize=axis_label_fontsize)
    ax.set_xlabel("Years", fontsize=axis_label_fontsize)
    ax.set_ylabel("Million ILS", fontsize=axis_label_fontsize)
    ax.set_ylim(0, y_max / 1_000_000.0)
    ax.grid(True)
    ax.legend(fontsize=legend_fontsize)

    # Year ticks from 0..years_projection inclusive
    ax.set_xticks(np.arange(0, years_projection + 1, 1))
    ax.set_xticklabels([str(y) for y in range(0, years_projection + 1)], fontsize=axis_tick_fontsize)
    ax.tick_params(axis='y', labelsize=axis_tick_fontsize)

    st.pyplot(fig, clear_figure=True)

# =========================
# INFO BOXES (right)
# =========================
with col_inputs:
    st.markdown("---")
    st.markdown(f"**Mortgage Amount:** {mortgage_amount:,.0f} ILS")
    st.markdown(f"**Monthly Mortgage Payment:** {mortgage_payment:,.0f} ILS")
    st.markdown(f"**Net Monthly Payment (payment − rent):** {net_monthly_after_rent:,.0f} ILS")

