"""
Phase 5 — Experimental track. Everything here is either a sandbox stub
(no real money, no real bank credentials) or explicitly labeled
"experimental" in its own response. None of it is wired into the
Phase 2-4 endpoints, so turning it off is just: don't mount this router.
"""
import random
from datetime import date, timedelta
import numpy as np
import pandas as pd


def sandbox_linked_accounts() -> dict:
    """
    Mocks what a Mono/Okra response might look like, so the frontend can be
    built against a stable shape before real credentials/compliance work
    happens. No network call, no real account, ever.
    """
    return {
        "mode": "SANDBOX — no real bank connection",
        "accounts": [
            {"institution": "Sandbox Bank", "account_type": "savings", "balance": 284500.00},
            {"institution": "Sandbox Bank", "account_type": "current", "balance": 62300.00},
        ],
        "note": "This is fabricated demo data. Real linking needs Mono/Okra "
                "credentials and NDPR-aware handling — see roadmap Phase 4/5.",
    }


def experimental_market_trend(symbol: str = "DEMO") -> dict:
    """
    Proof-of-concept only. Generates a synthetic random-walk price series
    (since no live market data source is connected here) and fits a naive
    moving-average trend — deliberately not sophisticated, because the
    point of this module is to demonstrate the labeling discipline, not
    to predict markets. A short-horizon backtest looking good is not
    evidence this holds live; that caveat ships with the response.
    """
    random.seed(hash(symbol) % 1000)
    prices = [100.0]
    for _ in range(59):
        prices.append(max(1, prices[-1] * (1 + random.uniform(-0.03, 0.03))))

    series = pd.Series(prices)
    ma_short = series.rolling(5).mean().iloc[-1]
    ma_long = series.rolling(20).mean().iloc[-1]
    signal = "upward bias" if ma_short > ma_long else "downward bias"

    return {
        "experimental": True,
        "not_investment_advice": True,
        "symbol": symbol,
        "data_source": "SYNTHETIC — random walk, not real market data",
        "naive_signal": signal,
        "reason": (
            f"5-day MA (₦{ma_short:.2f}) vs 20-day MA (₦{ma_long:.2f}) on synthetic "
            f"data suggests a {signal}. This is a toy signal on fake data, included "
            "only to show how an experimental module would be labeled and isolated "
            "from the advisory/analytics endpoints — not a real prediction."
        ),
    }


def ask_about_spending(txns: list[dict], question: str) -> dict:
    """
    Rule-based Q&A scoped strictly to the user's own uploaded spending data.
    No market opinions, no allocation advice, no external LLM call in this
    scaffold — just pattern-matching over their own numbers, which is the
    only thing the roadmap allows this module to touch.
    """
    q = question.lower()
    df = pd.DataFrame(txns)
    if df.empty:
        return {"answer": "You haven't uploaded any transactions yet."}

    df["amount"] = df["amount"].astype(float)
    spend = df[df["amount"] < 0].copy()
    spend["amount"] = spend["amount"].abs()

    if "most" in q or "biggest" in q or "top" in q:
        if spend.empty:
            return {"answer": "No spending recorded yet."}
        top = spend.groupby("category")["amount"].sum().idxmax()
        amt = spend.groupby("category")["amount"].sum().max()
        return {"answer": f"Your biggest spending category is {top}, at ₦{amt:,.0f}."}

    for category in spend["category"].unique() if not spend.empty else []:
        if category in q:
            amt = spend[spend["category"] == category]["amount"].sum()
            return {"answer": f"You've spent ₦{amt:,.0f} on {category} in this data."}

    if "total" in q or "how much" in q:
        return {"answer": f"Total spend in this data: ₦{spend['amount'].sum():,.0f}."}

    return {
        "answer": "I can only answer questions about your own uploaded spending "
        "data — try asking about a category, your total spend, or your biggest "
        "spending category."
    }
