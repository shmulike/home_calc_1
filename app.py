import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# -----------------------------
# SETTINGS
# -----------------------------
graph_width = 4  # Change this to make the graph wider/narrower

st.set_page_config(page_title="Real Estate vs Investment Simulator", layout="wide")
st.title("Real Estate & Investment Comparison Simulator")

# -----------------------------
# LAYOUT: Graph on left, controls on right
# -----------------------------
col_graph, col_inputs = st.columns([graph_width, 10 - graph_width])

with col_inputs:
    st.subheader("Property & Mortgage Parameters")

    apt1_value = st.number_input("First Apartment Value (ILS)", min_value=0.0, value=1_900_000.0, step=1000.0, format="%.0f", key="apt1_value")
    apt2_value = st.number_input("Second Apartment Value (ILS)", min_value=0.0, value=2_300_000.0, step=1000.0, format="%.0f", key="apt2_value")
    mortgage_amount = st.number_input("Mortgage Amount (ILS)", min_value=0.0, value=1_700_000.0, step=1000.0, format="%.0f", key="mortgage_amount")
    rent_monthly = st.number_input("Monthly Rent from Apt 1 (ILS)", min_value=0.0, value=4500.0, step=100.0, format="%.0f", key="rent_monthly")
    mortgage_rate = st.number_input("Mortgage Annual Rate (%)", min_value=0.0, value=4.0, step=0.1, format="%.2f", key="mortgage_rate")
    mortgage_years = st.number_input("Mortgage Years", min_value=1, value=25, step=1, key="mortgage_years")

    st.subheader("Growth & Returns")
    real_estate_growth = st.number_input("Annual Real Estate Growth (%)", min_value=0.0, value=3.0, step=0.1, format="%.2f", key="real_estate_growth")
    stock_return = st.number_input("Annual Stock Market Return (%)", min_value=0.0, value=6.5, step=0.1, format="%.2f", key="stock_return")

    st.subheader("Investment Parameters for Scenario 2")
    monthly_deposit = st.number_input("Monthly Stock Deposit (ILS)", min_value=0.0, value=7000.0, step=100.0, format="%.0f", key="monthly_deposit")
    years_projection = st.number_input("Projection Years", min_value=1, value=15, step=1, key="years_projection")

# -----------------------------
# CALCULATIONS
# -----------------------------
months = years_projection * 12
monthly_rate = mortgage_rate / 100 / 12
if mortgage_amount > 0 and mortgage_rate > 0:
    mortgage_payment = mortgage_amount * (monthly_rate * (1 + monthly_rate) ** (mortgage_years * 12)) / ((1 + monthly_rate) ** (mortgage_years * 12) - 1)
else:
    mortgage_payment = 0

net_monthly_payment = mortgage_payment - rent_monthly

# Scenario 1
apt1_values = []
apt2_values_s1 = []
total_assets_s1 = []
mortgage_debt_s1 = []

apt1_val = apt1_value
apt2_val = apt2_value
debt = mortgage_amount

for m in range(months + 1):
    apt1_values.append(apt1_val)
    apt2_values_s1.append(apt2_val)
    total_assets_s1.append(apt1_val + apt2_val)
    mortgage_debt_s1.append(debt)
    apt1_val *= (1 + real_estate_growth / 100 / 12)
    apt2_val *= (1 + real_estate_growth / 100 / 12)
    interest_payment = debt * monthly_rate
    principal_payment = mortgage_payment - interest_payment
    debt = max(0, debt - principal_payment)

# Scenario 2
apt2_values_s2 = []
stock_values_s2 = []
total_assets_s2 = []

apt2_val_s2 = apt2_value
stock_val = max(0, apt1_value - mortgage_amount)  # Initial difference from selling Apt 1

for m in range(months + 1):
    apt2_values_s2.append(apt2_val_s2)
    stock_values_s2.append(stock_val)
    total_assets_s2.append(apt2_val_s2 + stock_val)
    apt2_val_s2 *= (1 + real_estate_growth / 100 / 12)
    stock_val = stock_val * (1 + stock_return / 100 / 12) + monthly_deposit

# -----------------------------
# GRAPH
# -----------------------------
with col_graph:
    fig, ax = plt.subplots(figsize=(graph_width, 5))

    # Scenario 1
    ax.plot(np.array(total_assets_s1) / 1_000_000, label="Scenario 1: Total Assets", color="blue", linestyle="-")
    ax.plot(np.array(mortgage_debt_s1) / 1_000_000, label="Scenario 1: Mortgage Debt", color="blue", linestyle="--")

    # Scenario 2
    ax.plot(np.array(apt2_values_s2) / 1_000_000, label="Scenario 2: Apt 2 Value", color="orange", linestyle="--")
    ax.plot(np.array(stock_values_s2) / 1_000_000, label="Scenario 2: Stock Portfolio", color="orange", linestyle="-.")
    ax.plot(np.array(total_assets_s2) / 1_000_000, label="Scenario 2: Total Assets", color="orange", linestyle="-")

    ax.set_xlabel("Years")
    ax.set_ylabel("Million ILS")
    ax.set_title("Comparison of Scenarios Over Time")
    ax.legend()
    ax.grid(True)

    ax.set_xticks(range(0, months + 1, 12))
    ax.set_xticklabels([str(i) for i in range(0, years_projection + 1)])

    st.pyplot(fig)

# -----------------------------
# EXTRA INFO
# -----------------------------
with col_inputs:
    st.markdown(f"**Mortgage Amount:** {mortgage_amount:,.0f} ILS")
    st.markdown(f"**Mortgage Monthly Payment:** {mortgage_payment:,.0f} ILS")
    st.markdown(f"**Net Monthly Payment (after rent):** {net_monthly_payment:,.0f} ILS")
