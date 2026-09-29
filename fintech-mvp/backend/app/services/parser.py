"""
Phase 2 — Statement Ingestion.
Parses an uploaded CSV or PDF into normalized transaction rows and
applies a simple rule-based categorizer. This is intentionally basic;
Phase 3 replaces the categorizer with a trained model and adds
forecasting.
"""
import io
import re
from datetime import datetime, timedelta
import pandas as pd
import pdfplumber
import pytesseract

CATEGORY_RULES = {
    "transport": ["uber", "bolt", "taxi", "fuel", "petrol"],
    "food": ["restaurant", "food", "eatery", "kitchen", "supermarket", "grocery"],
    "subscriptions": ["netflix", "spotify", "prime", "subscription"],
    "utilities": ["electricity", "phcn", "dstv", "internet", "data bundle", "airtime"],
    "transfer": ["transfer", "pos", "atm withdrawal"],
    "income": ["salary", "credit alert", "deposit"],
    "checks": ["check #"],
}


def categorize(description: str) -> str:
    desc = description.lower()
    for category, keywords in CATEGORY_RULES.items():
        # short keywords ("pos") must be whole words; longer ones may be prefixes ("subscription(s)")
        if any(re.search(r"\b" + re.escape(k) + (r"\b" if len(k) <= 3 else ""), desc) for k in keywords):
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
# Strategies, in order: (1) ruled tables, (2) a stateful line parser that reads
# the Date/Description/Debits/Credits/Balance layout and infers debit vs credit
# from the running balance, (3) plain "date description amount" lines.

_MONEY = re.compile(r"[-+]?\(?[₦$£€]?\s?\d[\d,]*\.\d{2}(?![\d%])\)?")
_DATE = r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[\s-][A-Za-z]{3,9}[\s-]\d{2,4}"
_LINE_DATE = re.compile(rf"^({_DATE})\s+")
_TXN_HDR = re.compile(r"^date\s+description", re.I)
_STOP = re.compile(r"^(CHECKS|DAILY BALANCE|INTEREST CHARGE|READY RESERVE|ACCOUNT ACTIVITY|TRAN DATE)")
_CHECK = re.compile(rf"(\d{{3,6}})\s*\*?\s+({_DATE})\s+([₦$£€]?[\d,]+\.\d{{2}})")
_PERIOD_RE = re.compile(rf"period:?\s*({_DATE})\s*(?:to|To|TO|-)\s*({_DATE})", re.I)
_HEADERS = {
    "date": ("date",), "desc": ("description", "narration", "details", "particulars", "remarks"),
    "amount": ("amount", "value"), "debit": ("debit", "withdrawal", "dr"), "credit": ("credit", "deposit", "cr"),
}


def _clean_amount(raw):
    s = re.sub(r"[₦$£€,\s]", "", str(raw or ""))
    neg = s.startswith("(") and s.endswith(")")
    try:
        v = float(s.strip("()"))
    except ValueError:
        return None
    return -v if neg else v


def _detect_dayfirst(text):
    """Nigerian statements are day-first, US ones month-first. Decide from the
    whole document: a first part >12 means day-first, a second part >12 means month-first."""
    first = second = False
    for m in re.finditer(r"\b(\d{1,2})[/-](\d{1,2})[/-]\d{2,4}\b", text):
        first |= int(m[1]) > 12
        second |= int(m[2]) > 12
    return not (second and not first)


def _parse_date_any(raw, dayfirst=True):
    d, m = ("%d", "%m") if dayfirst else ("%m", "%d")
    fmts = [f"{d}/{m}/%Y", f"{d}/{m}/%y", f"{d}-{m}-%Y", f"{d}-{m}-%y", "%Y-%m-%d",
            "%d %b %Y", "%d %B %Y", "%d %b %y", "%d-%b-%Y", "%d-%B-%Y", "%d-%b-%y"]
    for fmt in fmts:
        try:
            return datetime.strptime(str(raw).strip(), fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _match_header(headers, key):
    for i, h in enumerate(headers):
        if any(re.search(rf"\b{re.escape(k)}s?\b", (h or "").strip().lower()) for k in _HEADERS[key]):
            return i
    return None


def _row(d, desc, amt):
    return {"date": d, "description": desc, "amount": amt, "category": categorize(desc)}


def _rows_from_table(table, dayfirst=True):
    if not table or len(table) < 2:
        return []
    h = [(c or "").strip().lower() for c in table[0]]
    di, ni, ai, dbi, cri = (_match_header(h, k) for k in ("date", "desc", "amount", "debit", "credit"))
    if di is None or ni is None or (ai is None and dbi is None and cri is None):
        return []
    need = max(i for i in (di, ni, ai, dbi, cri) if i is not None)
    rows = []
    for r in table[1:]:
        if not r or len(r) <= need:
            continue
        d, desc = _parse_date_any(r[di], dayfirst), str(r[ni] or "").strip()
        if not d or not desc:
            continue
        if ai is not None:
            amt = _clean_amount(r[ai])
        else:
            debit = _clean_amount(r[dbi]) if dbi is not None else None
            credit = _clean_amount(r[cri]) if cri is not None else None
            amt = abs(credit) if credit else -abs(debit) if debit else None
        if amt is not None:
            rows.append(_row(d, desc, amt))
    return rows


def _signed(desc, raw_token, amt):
    """Sign for an amount with no running balance to check against."""
    if raw_token.strip()[0] in "+-" or raw_token.strip().startswith("("):
        return amt
    return abs(amt) if categorize(desc) == "income" or re.search(r"\b(credit|deposit)", desc.lower()) else -abs(amt)


def _statement_bounds(text, dayfirst):
    """The statement's own declared period ("...for the period: 28-Sep-2025 To
    28-Sep-2026"), used to catch an implausible OCR digit misread in a
    transaction date (e.g. a single-digit year flip) that would otherwise
    silently corrupt that row's date."""
    m = _PERIOD_RE.search(text)
    if not m:
        return None
    a, b = _parse_date_any(m.group(1), dayfirst), _parse_date_any(m.group(2), dayfirst)
    return (min(a, b), max(a, b)) if a and b else None


def _rows_from_text(text, dayfirst=True):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    structured = any(_TXN_HDR.match(l) for l in lines)
    mode = None if structured else "txn"
    rows, pending, prev_bal, last_date = [], None, None, None
    bounds = _statement_bounds(text, dayfirst)
    last, last_i = None, -9  # a wrapped description can trail its row on the next line

    def finish(p):
        nonlocal prev_bal, last_date
        toks = p["amts"]
        desc = re.sub(r"\s+", " ", " ".join(p["desc"])).strip(" -|,:\t")
        vals = [_clean_amount(t) for t in toks]
        if not desc or not vals:
            return None
        if len(vals) >= 3:
            # Debit / Credit / Balance columns (common NG bank layout, and what
            # OCR'd tables collapse to). The balance delta is trusted over the
            # OCR'd amount digits whenever the two agree with what a real digit
            # misread would look like.
            debit, credit, bal = vals[-3], vals[-2], vals[-1]
            guess = (credit or 0) - (debit or 0)
            if prev_bal is not None and abs((bal - prev_bal) - guess) < 0.01:
                signed = bal - prev_bal
            else:
                signed = guess
            prev_bal = bal
        elif len(vals) == 2:  # [amount, running balance]
            amount, bal = vals[-2], vals[-1]
            if prev_bal is not None and abs(abs(bal - prev_bal) - abs(amount)) < 0.01:
                signed = bal - prev_bal
            else:
                signed = _signed(desc, toks[-2], amount)
            prev_bal = bal
        else:
            if re.search(r"balance|brought forward|b/f", desc.lower()):
                prev_bal = vals[0]
                return None
            signed = _signed(desc, toks[0], vals[0])
        # OCR occasionally drops a date's leading digit ("0-Oct-2025"), or
        # misreads a single digit into an implausible date (a year that lands
        # outside the statement's own declared period); in either case, keep
        # the transaction — and the balance chain — by reusing the last date
        # actually parsed rather than dropping or corrupting the row.
        d = _parse_date_any(p["date"], dayfirst)
        if d and bounds and not (bounds[0] - timedelta(days=3) <= d <= bounds[1] + timedelta(days=3)):
            d = None
        d = d or last_date
        if d:
            last_date = d
            rows.append(_row(d, desc, round(signed, 2)))
            return rows[-1]
        return None

    for i, line in enumerate(lines):
        if structured:
            if _TXN_HDR.match(line):
                mode, pending = "txn", None
                continue
            if _STOP.match(line):
                mode, pending = ("checks" if line.startswith("CHECKS") else None), None
                continue
        if mode == "checks":
            for num, ds, amt in _CHECK.findall(line):
                d = _parse_date_any(ds, dayfirst)
                if d:
                    rows.append(_row(d, f"Check #{num}", -abs(_clean_amount(amt))))
            continue
        if mode != "txn":
            continue
        dm = _LINE_DATE.match(line)
        money = [m.group() for m in _MONEY.finditer(line)]
        text_only = _MONEY.sub("", line[dm.end():] if dm else line).strip(" -|")
        if not dm and not pending and re.search(r"opening balance|brought forward|\bb/f\b", line.lower()):
            m = list(_MONEY.finditer(line))
            if m:
                prev_bal = _clean_amount(m[-1].group())
            continue
        if dm:
            pending = {"date": dm.group(1), "desc": [text_only], "amts": money}
            if money:
                last, last_i, pending = finish(pending), i, None
        elif pending:
            if money and not text_only:      # amount-only line closes a wrapped row
                pending["amts"] = money
                last, last_i, pending = finish(pending), i, None
            elif not money:                  # description continuation line
                pending["desc"].append(text_only)
        elif last and i == last_i + 1 and not money and ":" not in line and not line.startswith("Page"):
            last["description"] += " " + text_only
            last["category"] = categorize(last["description"])
            last = None
    return rows


OCR_MAX_PAGES = 40  # a scanned page takes several seconds on the server's CPU;
                     # this caps a single upload at a few minutes of processing


def _is_scanned(pdf) -> bool:
    """True if the PDF has no real text layer at all (i.e. it's a photo/scan of
    a statement, not an exported digital one) — extract_text/extract_tables
    return nothing useful on these, so they need OCR instead."""
    return all(len(p.chars) == 0 for p in pdf.pages)


def _ocr_text(pdf) -> str:
    if len(pdf.pages) > OCR_MAX_PAGES:
        raise ValueError(
            f"This scanned PDF has {len(pdf.pages)} pages, over the {OCR_MAX_PAGES}-page limit "
            "for OCR processing. Please split it into smaller files, or export a CSV instead."
        )
    # 200 DPI + psm 6 (assume one uniform block of text) was the fastest setting
    # in testing that didn't lose transactions to misreads on a real 22-page
    # statement; higher DPI barely improved accuracy further but cost much more time.
    return "\n".join(
        pytesseract.image_to_string(page.to_image(resolution=200).original, config="--psm 6")
        for page in pdf.pages
    )


def parse_pdf(file_bytes: bytes) -> list[dict]:
    """Best-effort bank statement PDF parser (see strategies above). Scanned
    (image-only) PDFs are OCR'd first; this is slow (multiple seconds per page
    on a constrained server) and only as accurate as the scan quality allows,
    with digit misreads guarded against via the running-balance reconciliation
    in _rows_from_text/_rows_from_table rather than trusted at face value."""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        if _is_scanned(pdf):
            text = _ocr_text(pdf)
            dayfirst = _detect_dayfirst(text)
            rows = _rows_from_text(text, dayfirst)
        else:
            text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            dayfirst = _detect_dayfirst(text)
            rows = [r for p in pdf.pages for t in (p.extract_tables() or []) for r in _rows_from_table(t, dayfirst)]
            rows = rows or _rows_from_text(text, dayfirst)
    if not rows:
        raise ValueError(
            "Couldn't find any recognizable transactions in this PDF. "
            "Try exporting a CSV instead, or check the statement has date/description/amount columns."
        )
    return rows
