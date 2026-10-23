
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

STATE_FILE = Path("state.json")
STARTING_CAPITAL = 10_000.0
TRADE_AMOUNT = 1_000.0
FEE_RATE = 0.001
BUY_DROP = 0.02
SELL_RISE = 0.02


def get_btc_price():
    response = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids": "bitcoin", "vs_currencies": "usd"},
        timeout=20,
    )
    response.raise_for_status()
    return float(response.json()["bitcoin"]["usd"])


def load_state(price):
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())

    return {
        "cash": STARTING_CAPITAL,
        "btc": 0.0,
        "reference_price": price,
        "trades": [],
    }


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, indent=2) + "\n"
    )


def main():
    price = get_btc_price()
    state = load_state(price)

    cash = float(state["cash"])
    btc = float(state["btc"])
    reference = float(state["reference_price"])
    action = "HOLD"

    if btc == 0 and price <= reference * (1 - BUY_DROP):
        amount = min(TRADE_AMOUNT, cash)

        if amount > 0:
            fee = amount * FEE_RATE
            quantity = (amount - fee) / price
            state["cash"] = round(cash - amount, 8)
            state["btc"] = btc + quantity
            action = "AUTO BUY"

    elif btc > 0 and price >= reference * (1 + SELL_RISE):
        proceeds = btc * price
        fee = proceeds * FEE_RATE
        state["cash"] = round(cash + proceeds - fee, 8)
        state["btc"] = 0.0
        action = "AUTO SELL"

    if action != "HOLD":
        state["trades"].append({
            "time_utc": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "price_usd": price,
            "btc": state["btc"] if action == "AUTO BUY" else btc,
            "fee_usd": (
                TRADE_AMOUNT * FEE_RATE
                if action == "AUTO BUY"
                else btc * price * FEE_RATE
            ),
        })
        state["reference_price"] = price

    portfolio = state["cash"] + state["btc"] * price
    pnl = portfolio - STARTING_CAPITAL

    save_state(state)

    print(f"BTC/USD: ${price:,.2f}")
    print(f"Action: {action}")
    print(f"Cash: ${state['cash']:,.2f}")
    print(f"BTC holdings: {state['btc']:.8f}")
    print(f"Portfolio: ${portfolio:,.2f}")
    print(f"Profit/Loss: ${pnl:,.2f}")
    print(f"Trades recorded: {len(state['trades'])}")


if __name__ == "__main__":
    main()
