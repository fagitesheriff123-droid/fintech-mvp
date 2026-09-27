"""
Phase 2 — Statement Ingestion.
Parses an uploaded CSV or PDF into normalized transaction rows and
applies a simple rule-based categorizer. This is intentionally basic;
Phase 3 replaces the categorizer with a trained model and adds
forecasting.
"""
import io
import re
from datetime import datetime
import pandas as pd
import pdfplumber

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


# --- PDF ingestion -----------------------------------------------------
# Bank statement PDFs vary a lot in layout. Two strategies, tried in order:
#  1. Structured tables (most bank-exported PDFs have real tables).
#  2. Line-by-line regex fallback for PDFs that are just laid-out text.

_DATE_HEADER_KEYWORDS = ("date",)
_DESC_HEADER_KEYWORDS = ("description", "narration", "details", "particulars", "remarks")
_AMOUNT_HEADER_KEYWORDS = ("amount", "value")
_DEBIT_HEADER_KEYWORDS = ("debit", "withdrawal", "dr")
_CREDIT_HEADER_KEYWORDS = ("credit", "deposit", "cr")

_LINE_DATE_RE = re.compile(
    r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{1,2}-\d{1,2}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4})"
)
_LINE_AMOUNT_RE = re.compile(r"[-+]?₦?\s?[\d,]+\.\d{2}")


def _clean_amount(raw):
    if raw is None:
        return None
    s = str(raw).strip().replace("₦", "").replace(",", "").replace(" ", "")
    if not s or s in {"-", "—"}:
        return None
    negative = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        val = float(s)
    except ValueError:
        return None
    return -val if negative else val


def _parse_date_any(raw):
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(str(raw).strip(), fmt).date()
        except (ValueError, TypeError):
            continue
    try:
        return pd.to_datetime(raw, dayfirst=True).date()
    except Exception:
        return None


def _match_header(headers, keywords):
    for i, h in enumerate(headers):
        h = (h or "").strip().lower()
        if any(re.search(rf"\b{re.escape(k)}\b", h) for k in keywords):
            return i
    return None


def _rows_from_table(table):
    if not table or len(table) < 2:
        return []
    headers = [(c or "").strip().lower() for c in table[0]]

    date_i = _match_header(headers, _DATE_HEADER_KEYWORDS)
    desc_i = _match_header(headers, _DESC_HEADER_KEYWORDS)
    amount_i = _match_header(headers, _AMOUNT_HEADER_KEYWORDS)
    debit_i = _match_header(headers, _DEBIT_HEADER_KEYWORDS)
    credit_i = _match_header(headers, _CREDIT_HEADER_KEYWORDS)

    if date_i is None or desc_i is None or (amount_i is None and debit_i is None and credit_i is None):
        return []  # doesn't look like a statement table — let the caller fall back

    needed_indices = [i for i in (date_i, desc_i, amount_i, debit_i, credit_i) if i is not None]
    rows = []
    for raw_row in table[1:]:
        if not raw_row or len(raw_row) <= max(needed_indices):
            continue
        d = _parse_date_any(raw_row[date_i])
        desc = str(raw_row[desc_i] or "").strip()
        if not d or not desc:
            continue

        if amount_i is not None:
            amt = _clean_amount(raw_row[amount_i])
        else:
            debit = _clean_amount(raw_row[debit_i]) if debit_i is not None else None
            credit = _clean_amount(raw_row[credit_i]) if credit_i is not None else None
            if credit:
                amt = abs(credit)
            elif debit:
                amt = -abs(debit)
            else:
                amt = None
        if amt is None:
            continue

        rows.append({"date": d, "description": desc, "amount": amt, "category": categorize(desc)})
    return rows


def _rows_from_text(text):
    rows = []
    for line in text.splitlines():
        date_match = _LINE_DATE_RE.search(line)
        if not date_match:
            continue
        amount_matches = list(_LINE_AMOUNT_RE.finditer(line))
        if not amount_matches:
            continue
        amount_match = amount_matches[-1]

        d = _parse_date_any(date_match.group(0))
        if not d:
            continue

        desc = (line[date_match.end():amount_match.start()]).strip(" -|,:\t")
        if not desc:
            continue

        amt = _clean_amount(amount_match.group(0))
        if amt is None:
            continue
        if amount_match.group(0).strip()[0] not in "+-":
            # No explicit sign in the source text — infer it the same way
            # everything else in this app decides income vs. spend.
            amt = abs(amt) if categorize(desc) == "income" else -abs(amt)

        rows.append({"date": d, "description": desc, "amount": amt, "category": categorize(desc)})
    return rows


def parse_pdf(file_bytes: bytes) -> list[dict]:
    """
    Best-effort bank statement PDF parser. Tries real tables first
    (most bank-exported PDFs have them), falls back to regex-scanning
    text lines for PDFs that are just laid-out text.
    """
    rows = []
    all_text = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                rows.extend(_rows_from_table(table))
            all_text.append(page.extract_text() or "")

    if not rows:
        rows = _rows_from_text("\n".join(all_text))

    if not rows:
        raise ValueError(
            "Couldn't find any recognizable transactions in this PDF. "
            "Try exporting a CSV instead, or check the statement has date/description/amount columns."
        )

    return rows
