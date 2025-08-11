import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# =========================
# DISPLAY / STYLE SETTINGS
# =========================
graph_col_width       = 7   # left column width (graph). Right column gets the rest (out of 10)
plot_width            = 9   # matplotlib figure width
plot_height           = 6   # matplotlib figure height
legend_fontsize       = 11  # legend font size
axis_label_fontsize   = 12  # axis labels & title font size
axis_tick_fontsize    = 10  # axis tick numbers font size

st.set_page_config(page_title="Keep vs Sell: Apartment vs Stocks", layout="wide")
st.title("Keep the Apartment & Pay Mortgage vs Sell and Invest")

# =========================
# LAYOUT: Graph (left) | Inputs (right)
# =========================
col_graph, col_inputs = st.columns([graph_col_width, 10 - graph_col_width])

with col_inputs:
    # ---------------------
    # General
    # ---------------------
    st.header("General")
    years_projection = st.number_input(
        "Projection Years",
        min_value=1, value=15, step=1, key="years_projection"
    )

    # ---------------------
    # Property Parameters
    # ---------------------
    st.header("Property Parameters")
    apt_value = st.number_input(
        "Apartment Value (ILS)",
        min_value=0.0, value=1_900_000.0, step=10_000.0, format="%.0f", key="apt_value"
    )
    re_growth_pct = st.number_input(
        "Annual Real Estate Growth (%)",
        min_value=0.0, value=3.00, step=0.10, format="%.2f", key="re_growth_pct"
    )
    monthly_rent = st.number_input(
        "Monthly Rent income (ILS)",
        min_value=0.0, value=4_500.0, step=100.0, format="%.0f", key="monthly_rent"
    )

    # ---------------------
    # Mortgage Parameters
    # ---------------------
    st.header("Mortgage Parameters")
    mortgage_amount = st.number_input(
        "Mortgage Amount (ILS)",
        min_value=0.0, value=1_700_000.0, step=10_000.0, format="%.0f", key="mortgage_amount"
    )
    mortgage_years = st.number_input(
        "Mortgage Years",
        min_value=1, value=25, step=1, key="mortgage_years"
    )
    mortgage_rate_pct = st.number_input(
        "Mortgage Annual Rate (%)",
        min_value=0.0, value=4.00, step=0.10, format="%.2f", key="mortgage_rate_pct"
    )
    
    # ---------------------
    # Stock Market
    # ---------------------
    st.header("Stock Market")
    initial_deposit = st.number_input(
        "Initial deposit (ILS)",
        min_value=0.0, value=200_000.0, step=10_000.0, format="%.0f", key="initial_deposit"
    )
    monthly_deposit = st.number_input(
        "Monthly Deposit (ILS)",
        min_value=0.0, value=7_000.0, step=100.0, format="%.0f", key="monthly_deposit"
    )
    stock_return_pct = st.number_input(
        "Annual Stock Market Return (%)",
        min_value=0.0, value=6.50, step=0.10, format="%.2f", key="stock_return_pct"
    )

# =========================
# CALCULATIONS
# =========================
months = int(years_projection) * 12
re_growth = re_growth_pct / 100.0
stock_return = stock_return_pct / 100.0

# Mortgage monthly payment (standard annuity)
monthly_rate = (mortgage_rate_pct / 100.0) / 12.0
n_pay = int(mortgage_years) * 12
if mortgage_amount > 0 and monthly_rate > 0 and n_pay > 0:
    mortgage_payment = mortgage_amount * (monthly_rate * (1 + monthly_rate) ** n_pay) / ((1 + monthly_rate) ** n_pay - 1)
elif mortgage_amount > 0 and monthly_rate == 0 and n_pay > 0:
    mortgage_payment = mortgage_amount / n_pay
else:
    mortgage_payment = 0.0

net_monthly_after_rent = mortgage_payment - monthly_rent  # info only (doesn't change amortization)

# --- Scenario 1: Keep apartment, rent, pay mortgage ---
apt_series_s1 = np.zeros(months + 1)
debt_series_s1 = np.zeros(months + 1)

# apartment value growth
apt_val = float(apt_value)
for m in range(months + 1):
    apt_series_s1[m] = apt_val
    apt_val *= (1 + re_growth / 12.0)

# mortgage amortization (no extra principal by default)
debt = float(mortgage_amount)
for m in range(months + 1):
    debt_series_s1[m] = max(0.0, debt)
    interest_part = debt * monthly_rate
    principal_part = mortgage_payment - interest_part
    principal_part = max(0.0, principal_part)
    debt = max(0.0, debt - principal_part)

# --- Scenario 2: Sell and invest in stock market (no apartment) ---
equity_series_s2 = np.zeros(months + 1)
amt = float(initial_deposit)
equity_series_s2[0] = amt
for m in range(1, months + 1):
    amt = amt * (1 + stock_return / 12.0) + monthly_deposit
    equity_series_s2[m] = amt

years_axis = np.arange(months + 1) / 12.0

# Shared Y max (in ILS)
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

    # Ticks (years)
    ax.set_xticks(np.arange(0, months + 1, 12))
    ax.set_xticklabels([str(y) for y in range(0, years_projection + 1)], fontsize=axis_tick_fontsize)
    ax.tick_params(axis='y', labelsize=axis_tick_fontsize)

    st.pyplot(fig, clear_figure=True)

# =========================
# INFO BOXES (right)
# =========================
with col_inputs:
    st.markdown("---")
    st.markdown(f"**Mortgage Amount:** {mortgage_amount:,.0f} ILS")
    st.markdown(f"**Monthly Mortgage Payment (no extra principal):** {mortgage_payment:,.0f} ILS")
    st.markdown(f"**Net Monthly Payment after Rent (payment − rent):** {net_monthly_after_rent:,.0f} ILS")
