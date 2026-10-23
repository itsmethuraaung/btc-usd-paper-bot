
import streamlit as st
import requests

st.set_page_config(
    page_title="BTC/USD Paper Trading Bot",
    page_icon="₿",
    layout="wide"
)

STARTING_CAPITAL = 10000.0
FEE_RATE = 0.001

st.title("₿ BTC/USD Paper Trading Bot")
st.caption("Paper Trading Simulation — No real money")

@st.cache_data(ttl=30)
def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    response = requests.get(
        url,
        params={"ids": "bitcoin", "vs_currencies": "usd"},
        timeout=15
    )
    response.raise_for_status()
    return float(response.json()["bitcoin"]["usd"])

if "cash" not in st.session_state:
    st.session_state.cash = STARTING_CAPITAL
    st.session_state.btc = 0.0
    st.session_state.trades = []

try:
    price = get_btc_price()
except Exception:
    price = None
    st.error("BTC price unavailable. Please try again later.")

if price is not None:
    st.metric("Live BTC Price", f"${price:,.2f}")

    cash = st.session_state.cash
    btc = st.session_state.btc
    value = cash + btc * price
    pnl = value - STARTING_CAPITAL

    a, b, c, d = st.columns(4)
    a.metric("Starting Capital", "$10,000.00")
    b.metric("Cash Balance", f"${cash:,.2f}")
    c.metric("BTC Holdings", f"{btc:.8f}")
    d.metric("Portfolio Value", f"${value:,.2f}", f"{pnl:+,.2f} USD")

    st.subheader("Paper Trading")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Buy BTC ($1,000)", use_container_width=True):
            amount = min(1000.0, st.session_state.cash)
            if amount > 0:
                fee = amount * FEE_RATE
                quantity = (amount - fee) / price
                st.session_state.cash -= amount
                st.session_state.btc += quantity
                st.session_state.trades.append({
                    "Action": "BUY",
                    "Price USD": price,
                    "BTC": quantity,
                    "Fee USD": fee
                })
                st.rerun()

    with col2:
        if st.button("Sell All BTC", use_container_width=True):
            quantity = st.session_state.btc
            if quantity > 0:
                proceeds = quantity * price
                fee = proceeds * FEE_RATE
                st.session_state.cash += proceeds - fee
                st.session_state.btc = 0.0
                st.session_state.trades.append({
                    "Action": "SELL",
                    "Price USD": price,
                    "BTC": quantity,
                    "Fee USD": fee
                })
                st.rerun()

    st.subheader("Trade History")
    if st.session_state.trades:
        st.dataframe(
            st.session_state.trades,
            use_container_width=True
        )
    else:
        st.info("No trades yet. Click Buy BTC to test the simulation.")

    st.caption(
        "Educational simulation only. This is not financial advice. "
        "Simulation data may reset when the app restarts."
    )
