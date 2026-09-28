"""Quick quality report for one bank statement (PDF or CSV).
  python -m eval.statement_report statement.pdf [--opening 445.28 --closing 942.82]
--opening/--closing (from the statement itself) let you check the parse reconciles."""
import sys
from collections import Counter
from app.services.parser import parse_pdf, parse_csv
from app.services import analytics as A

path = sys.argv[1]
arg = lambda k: float(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else None
rows = (parse_pdf if path.lower().endswith(".pdf") else parse_csv)(open(path, "rb").read())
n, cats = len(rows), Counter(r["category"] for r in rows)
spend = [r for r in rows if r["amount"] < 0]
txns = [dict(r, id=i) for i, r in enumerate(rows)]
print(f"rows {n} | {min(r['date'] for r in rows)} -> {max(r['date'] for r in rows)}")
print(f"credits {sum(r['amount'] for r in rows if r['amount'] > 0):,.2f} | debits {-sum(r['amount'] for r in spend):,.2f}")
print(f"categories {dict(cats)} | 'other' = {100*cats['other']/n:.1f}% of rows, {100*sum(r['category']=='other' for r in spend)/max(1,len(spend)):.1f}% of spend rows")
print(f"anomalies flagged {len(A.detect_anomalies(txns))}/{n} | health {A.health_score(txns)['score']}")
if arg("--opening") is not None and arg("--closing") is not None:
    chk = sum(r["amount"] for r in rows if r["description"].startswith("Check #"))
    net = sum(r["amount"] for r in rows)
    print(f"reconcile: opening + all rows = {arg('--opening') + net:,.2f} | excluding checks = {arg('--opening') + net - chk:,.2f} | statement closing {arg('--closing'):,.2f}")
