"""
Phase 4 — Scenario Simulator, Goal-Based Tracking, Debt Payoff Helper.

Everything here works off the user's own historical numbers or numbers
they enter directly (debts). No market data, no allocation advice —
stays out of investment-advice territory by construction.
"""
from datetime import date
import pandas as pd


def _monthly_savings_rate(txns: list[dict]) -> tuple[float, float, float]:
    """Returns (avg_monthly_income, avg_monthly_spend, avg_monthly_savings)."""
    if not txns:
        return 0.0, 0.0, 0.0
    df = pd.DataFrame(txns)
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M")
    months = df["month"].nunique() or 1

    income = df[df["amount"] > 0]["amount"].sum() / months
    spend = df[df["amount"] < 0]["amount"].abs().sum() / months
    return income, spend, income - spend


def simulate_scenario(txns: list[dict], extra_savings_per_month: float) -> dict:
    income, spend, current_savings = _monthly_savings_rate(txns)
    new_savings = current_savings + extra_savings_per_month
    new_spend = max(0, spend - extra_savings_per_month)

    return {
        "current_avg_monthly_savings": round(current_savings, 2),
        "projected_monthly_savings": round(new_savings, 2),
        "implied_monthly_spend": round(new_spend, 2),
        "reason": (
            f"Based on your avg monthly income (₦{income:,.0f}) and spend "
            f"(₦{spend:,.0f}), saving an extra ₦{extra_savings_per_month:,.0f}/mo "
            f"would take monthly savings from ₦{current_savings:,.0f} to ₦{new_savings:,.0f}."
        ),
    }


def goal_projection(txns: list[dict], target_amount: float, target_date: date) -> dict:
    _, _, current_savings = _monthly_savings_rate(txns)
    months_left = max(
        1, (target_date.year - date.today().year) * 12 + (target_date.month - date.today().month)
    )
    required_monthly = target_amount / months_left
    feasible = current_savings >= required_monthly

    gap = required_monthly - current_savings
    reason = (
        f"Reaching ₦{target_amount:,.0f} by {target_date} needs ₦{required_monthly:,.0f}/mo. "
        + (
            f"You're currently saving about ₦{current_savings:,.0f}/mo — on track."
            if feasible
            else f"You're currently saving about ₦{current_savings:,.0f}/mo — "
            f"about ₦{gap:,.0f}/mo short."
        )
    )
    return {
        "months_left": months_left,
        "required_monthly_savings": round(required_monthly, 2),
        "current_avg_monthly_savings": round(current_savings, 2),
        "feasible": feasible,
        "reason": reason,
    }


def debt_payoff_order(debts: list[dict], strategy: str = "avalanche") -> dict:
    """
    avalanche: highest interest rate first (mathematically optimal)
    snowball: smallest balance first (behaviorally easier to stick with)
    """
    if strategy not in {"avalanche", "snowball"}:
        strategy = "avalanche"

    key = (lambda d: -d["interest_rate"]) if strategy == "avalanche" else (lambda d: d["balance"])
    ordered = sorted(debts, key=key)

    total_interest_est = sum(d["balance"] * d["interest_rate"] / 100 for d in debts)

    reason = (
        "Avalanche order — pay minimums on everything, throw extra at the highest "
        "interest rate first. Minimizes total interest paid."
        if strategy == "avalanche"
        else "Snowball order — pay minimums on everything, throw extra at the "
        "smallest balance first. Clears accounts faster, which tends to stick better."
    )

    return {
        "strategy": strategy,
        "order": [d["name"] for d in ordered],
        "details": ordered,
        "estimated_annual_interest_if_untouched": round(total_interest_est, 2),
        "reason": reason,
    }
