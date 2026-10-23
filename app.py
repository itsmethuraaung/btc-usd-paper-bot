
import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="BTC/USD Auto Paper Trader",
    page_icon="₿",
    layout="wide"
)

STARTING_CAPITAL = 10000.0
TRADE_AMOUNT = 1000.0
FEE_RATE = 0.001
BUY_DROP = 0.02
SELL_RISE = 0.02

st.title("₿ BTC/USD Auto Paper Trading Bot")
st.caption("Simulation only — no real money or exchange orders")

# Refresh dashboard every 30 seconds
st_autorefresh(interval=30_000, key="dashboard_refresh")

@st.cache_data(ttl=25)
def get_btc_price():
    response = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids": "bitcoin", "vs_currencies": "usd"},
        timeout=15
    )
    response.raise_for_status()
    return float(response.json()["bitcoin"]["usd"])

# Initialize simulation state
if "cash" not in st.session_state:
    st.session_state.cash = STARTING_CAPITAL
    st.session_state.btc = 0.0
    st.session_state.trades = []
    st.session_state.reference_price = None
    st.session_state.last_auto_action = "NONE"

try:
    price = get_btc_price()
except Exception:
    price = None
    st.error("Unable to retrieve BTC price. Please retry later.")

if price is not None:
    if st.session_state.reference_price is None:
        st.session_state.reference_price = price

    reference = st.session_state.reference_price

    # Rule-based automatic paper trading
    if price <= reference * (1 - BUY_DROP):
        amount = min(TRADE_AMOUNT, st.session_state.cash)
        if amount >= TRADE_AMOUNT and st.session_state.last_auto_action != "BUY":
            fee = amount * FEE_RATE
            quantity = (amount - fee) / price
            st.session_state.cash -= amount
            st.session_state.btc += quantity
            st.session_state.trades.append({
                "Time (UTC)": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M:%S"),
                "Action": "AUTO BUY",
                "Price USD": price,
                "BTC": quantity,
                "Fee USD": fee
            })
            st.session_state.last_auto_action = "BUY"

    elif price >= reference * (1 + SELL_RISE):
        if st.session_state.btc > 0 and st.session_state.last_auto_action != "SELL":
            quantity = st.session_state.btc
            proceeds = quantity * price
            fee = proceeds * FEE_RATE
            st.session_state.cash += proceeds - fee
            st.session_state.btc = 0.0
            st.session_state.trades.append({
                "Time (UTC)": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M:%S"),
                "Action": "AUTO SELL",
                "Price USD": price,
                "BTC": quantity,
                "Fee USD": fee
            })
            st.session_state.last_auto_action = "SELL"

    portfolio_value = st.session_state.cash + st.session_state.btc * price
    pnl = portfolio_value - STARTING_CAPITAL
    pnl_pct = pnl / STARTING_CAPITAL * 100

    st.metric("Live BTC/USD", f"${price:,.2f}")
    st.metric("Reference Price", f"${reference:,.2f}")

    if price <= reference * (1 - BUY_DROP):
        st.warning("BUY threshold reached")
    elif price >= reference * (1 + SELL_RISE):
        st.success("SELL threshold reached")
    else:
        st.info("HOLD — waiting for price threshold")

    st.subheader("Portfolio Dashboard")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Starting Capital", f"${STARTING_CAPITAL:,.2f}")
    col2.metric("Cash Balance", f"${st.session_state.cash:,.2f}")
    col3.metric("BTC Holdings", f"{st.session_state.btc:.8f}")
    col4.metric("Portfolio Value", f"${portfolio_value:,.2f}", f"{pnl_pct:+.2f}%")

    st.metric("Profit / Loss", f"${pnl:,.2f}")

    st.subheader("Auto Trading Controls")
    st.write("Automatic trading is enabled for this simulation.")
    st.write(f"Buy amount: ${TRADE_AMOUNT:,.2f} | Fee: {FEE_RATE * 100:.2f}%")
    st.write("Rule: Buy after a 2% drop or sell holdings after a 2% rise from reference price.")

    if st.button("Reset Simulation"):
        st.session_state.cash = STARTING_CAPITAL
        st.session_state.btc = 0.0
        st.session_state.trades = []
        st.session_state.reference_price = price
        st.session_state.last_auto_action = "NONE"
        st.rerun()

    st.subheader("Trade History")
    if st.session_state.trades:
        st.dataframe(
            pd.DataFrame(st.session_state.trades),
            use_container_width=True
        )
    else:
        st.info("No automatic trades yet. The bot waits for its price threshold.")

    st.caption(
        "Educational simulation only. Refreshing the app does not guarantee "
        "continuous execution; state may reset after a restart. "
        "This strategy is not a reliable prediction of future prices."
    )
