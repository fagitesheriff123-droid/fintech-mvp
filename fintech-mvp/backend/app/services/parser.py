"""
Phase 2 — Statement Ingestion.
Parses an uploaded CSV into normalized transaction rows and applies a
simple rule-based categorizer. This is intentionally basic; Phase 3
replaces the categorizer with a trained model and adds forecasting.
"""
import io
import pandas as pd

CATEGORY_RULES = {
    "transport": ["uber", "bolt", "taxi", "fuel", "petrol"],
    "food": ["restaurant", "food", "eatery", "kitchen", "supermarket", "grocery"],
    "subscriptions": ["netflix", "spotify", "prime", "subscription"],
    "utilities": ["electricity", "phcn", "dstv", "internet", "data bundle", "airtime"],
    "transfer": ["transfer", "pos", "atm withdrawal"],
    "income": ["salary", "credit alert", "deposit"],
}


def categorize(description: str) -> str:
    desc = description.lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(k in desc for k in keywords):
            return category
    return "other"


def parse_csv(file_bytes: bytes) -> list[dict]:
    """
    Expects a CSV with at least: date, description, amount columns
    (case-insensitive). Returns normalized, categorized rows.
    """
    df = pd.read_csv(io.BytesIO(file_bytes))
    df.columns = [c.strip().lower() for c in df.columns]

    required = {"date", "description", "amount"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["amount"])
    df["category"] = df["description"].astype(str).apply(categorize)

    return df[["date", "description", "amount", "category"]].to_dict(orient="records")
