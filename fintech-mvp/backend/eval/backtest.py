"""Walk-forward backtest of the *deployed* forecast (analytics.forecast_next_month).

For each month t >= min_history: fit on months < t, predict month t, compare to what
actually happened, per category. Reports MAPE (roadmap target <15%) and WAPE, next to two
naive baselines (last month, average of history) so "good" has something to beat.

  python -m eval.backtest statement.csv            # CSV: date, description, amount
  python -m eval.backtest export.json              # JSON from GET /transactions/export
  python -m eval.backtest --selftest               # checks the maths on known answers
"""
import json, sys
import pandas as pd
from app.services.analytics import forecast_next_month
from app.services.parser import categorize


def load(path):
    if path.endswith(".json"):
        df = pd.DataFrame(json.load(open(path))["transactions"])
    else:
        df = pd.read_csv(path); df.columns = [c.strip().lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    if "category" not in df:
        df["category"] = df["description"].astype(str).apply(categorize)
    df["id"] = range(len(df)); df["description"] = df.get("description", "")
    return df


def backtest(df, min_history=3):
    df = df.copy(); df["month"] = df["date"].dt.to_period("M")
    months = sorted(df["month"].unique())
    if len(months) < min_history + 1:
        return {"status": "insufficient_history", "months": len(months), "needed": min_history + 1}
    spend = df[df["amount"] < 0].assign(amount=lambda d: d["amount"].abs())
    monthly = spend.groupby(["category", "month"])["amount"].sum()
    pts = []
    for t in months[min_history:]:
        hist = df[df["month"] < t]
        pred = {r["category"]: r["predicted_amount"] for r in forecast_next_month(hist.to_dict("records"))}
        for cat, actual in monthly.xs(t, level="month").items():
            past = monthly.loc[cat][monthly.loc[cat].index < t] if cat in monthly.index.get_level_values(0) else []
            if cat in pred and len(past):
                pts.append((str(t), cat, actual, pred[cat], past.iloc[-1], past.mean()))
    if not pts:
        return {"status": "no_comparable_points", "months": len(months)}
    p = pd.DataFrame(pts, columns=["month", "category", "actual", "model", "last", "mean"])
    out = {"status": "ok", "months": len(months), "points": len(p), "splits": p["month"].nunique()}
    for name in ("model", "last", "mean"):
        e = (p[name] - p["actual"]).abs()
        out[name] = {"MAPE_%": round(float((e / p["actual"]).mean() * 100), 1), "WAPE_%": round(float(e.sum() / p["actual"].sum() * 100), 1)}
    return out


def _tx(month, cat, amt):
    return {"date": f"{month}-15", "description": cat, "amount": -amt, "category": cat}


def selftest():
    # Known answer 1: perfectly linear spend -> the linear model should be exact (MAPE 0).
    lin = pd.DataFrame([_tx(f"2026-{m:02d}", "food", 1000 + 100 * m) for m in range(1, 7)])
    lin["date"] = pd.to_datetime(lin["date"]); lin["id"] = range(len(lin))
    r = backtest(lin); assert r["status"] == "ok" and r["model"]["MAPE_%"] == 0.0, r
    # Known answer 2, by hand: history 100,100,100 -> predicts 100; actual 200 -> APE 50%.
    step = pd.DataFrame([_tx(f"2026-{m:02d}", "food", a) for m, a in zip(range(1, 5), (100, 100, 100, 200))])
    step["date"] = pd.to_datetime(step["date"]); step["id"] = range(len(step))
    r = backtest(step); assert r["points"] == 1 and r["model"]["MAPE_%"] == 50.0 and r["last"]["MAPE_%"] == 50.0, r
    # Too little data must say so, not print a number.
    assert backtest(step.head(2))["status"] == "insufficient_history"
    print("selftest: 3/3 passed")


if __name__ == "__main__":
    if "--selftest" in sys.argv: selftest()
    else: print(json.dumps(backtest(load(sys.argv[1])), indent=2))
