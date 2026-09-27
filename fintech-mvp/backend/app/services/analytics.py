"""
Phase 3 — Predictive Analytics.

Three pieces, kept simple on purpose (no Prophet — a linear trend on
monthly per-category totals is honest about how little history a new
user has, and is easy to explain in plain language):

1. forecast_next_month(txns)   -> predicted spend per category
2. detect_anomalies(txns)      -> flagged transactions + reason
3. health_score(txns)          -> one composite 0-100 number
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest


def _to_df(txns: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(txns)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M")
    return df


def forecast_next_month(txns: list[dict]) -> list[dict]:
    df = _to_df(txns)
    if df.empty:
        return []

    spend = df[df["amount"] < 0].copy()
    spend["amount"] = spend["amount"].abs()
    monthly = spend.groupby(["category", "month"])["amount"].sum().reset_index()

    results = []
    for category, group in monthly.groupby("category"):
        group = group.sort_values("month")
        y = group["amount"].values
        if len(y) == 1:
            predicted = y[0]
            reason = f"Only one month of {category} data — using that as the estimate."
        else:
            x = np.arange(len(y))
            slope, intercept = np.polyfit(x, y, 1)
            predicted = max(0, slope * len(y) + intercept)
            trend = "rising" if slope > 0 else "falling" if slope < 0 else "flat"
            reason = (
                f"{category.capitalize()} spend has been {trend} over the last "
                f"{len(y)} months (avg ₦{y.mean():,.0f}/mo)."
            )
        results.append(
            {
                "category": category,
                "predicted_amount": round(float(predicted), 2),
                "reason": reason,
            }
        )
    return sorted(results, key=lambda r: -r["predicted_amount"])


def detect_anomalies(txns: list[dict]) -> list[dict]:
    df = _to_df(txns)
    if len(df) < 5:
        return []

    flagged = []
    for category, group in df.groupby("category"):
        if len(group) < 4:
            continue
        amounts = group["amount"].abs().values.reshape(-1, 1)
        model = IsolationForest(contamination=0.15, random_state=42)
        preds = model.fit_predict(amounts)
        mean, std = amounts.mean(), amounts.std() or 1

        for (_, row), pred, amt in zip(group.iterrows(), preds, amounts.flatten()):
            if pred == -1:
                direction = "higher" if amt > mean else "lower"
                z = (amt - mean) / std
                flagged.append(
                    {
                        "transaction_id": row["id"],
                        "description": row["description"],
                        "amount": row["amount"],
                        "category": category,
                        "reason": (
                            f"₦{amt:,.0f} is {direction} than your usual "
                            f"{category} spend (avg ₦{mean:,.0f}, ~{abs(z):.1f}x off pattern)."
                        ),
                    }
                )
    return flagged


def health_score(txns: list[dict]) -> dict:
    df = _to_df(txns)
    if df.empty:
        return {"score": None, "reason": "Not enough data yet."}

    income = df[df["amount"] > 0]["amount"].sum()
    spend = df[df["amount"] < 0]["amount"].abs().sum()

    if income == 0:
        return {"score": None, "reason": "No income detected in this data yet."}

    savings_rate = max(0, (income - spend) / income)
    category_counts = df[df["amount"] < 0]["category"].nunique()
    diversification_penalty = 0 if category_counts <= 6 else 5

    score = round(min(100, savings_rate * 100) - diversification_penalty)
    score = max(0, score)

    if score >= 70:
        verdict = "healthy savings rate"
    elif score >= 40:
        verdict = "moderate — spending is eating into most of your income"
    else:
        verdict = "spending is close to or above income"

    return {
        "score": score,
        "savings_rate": round(savings_rate * 100, 1),
        "reason": f"Savings rate of {savings_rate*100:.0f}% this period — {verdict}.",
    }
