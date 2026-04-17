from __future__ import annotations

import io
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Iterable, Optional


class StatementParseError(ValueError):
    pass


_DATE_RE = re.compile(r"^(?P<d>\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b")
_AMOUNT_RE = re.compile(r"(?P<a>\(?-?[\d,]+(?:\.\d{1,2})?\)?)\s*(?P<suffix>CR|DR)?\s*$", re.IGNORECASE)
_AMOUNT_TOKEN_RE = re.compile(r"^\(?-?[\d,]+(?:\.\d{1,2})?\)?$")


def _parse_date(value: str) -> date:
    raw = (value or "").strip()
    if not raw:
        raise StatementParseError("Missing date")
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%y", "%d-%m-%y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise StatementParseError(f"Invalid date: {value}")


def _parse_amount_token(token: str) -> Decimal:
    raw = (token or "").strip()
    if not raw:
        raise StatementParseError("Missing amount")
    neg = False
    if raw.startswith("(") and raw.endswith(")"):
        neg = True
        raw = raw[1:-1].strip()
    raw = raw.replace(",", "")
    raw = raw.replace("₹", "").replace("$", "").replace("€", "").replace("£", "").strip()
    try:
        amt = Decimal(raw)
    except (InvalidOperation, ValueError):
        raise StatementParseError(f"Invalid amount: {token}")
    if neg:
        amt = -amt
    return amt


def _collapse_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


@dataclass(frozen=True)
class ParsedStatementRow:
    transaction_date: date
    value_date: Optional[date]
    description: str
    debit: Optional[Decimal]
    credit: Optional[Decimal]
    reference: Optional[str]
    balance: Optional[Decimal]


def _iter_text_lines(pdf_text: str) -> Iterable[str]:
    for line in (pdf_text or "").splitlines():
        line = _collapse_spaces(line)
        if not line:
            continue
        yield line


def _guess_reference(description: str) -> Optional[str]:
    # Common patterns: "Ref: XYZ", "RRN 123", "UTR ABC", "NEFT-123", etc.
    desc = description or ""
    m = re.search(r"\b(ref(?:erence)?|rrn|utr)\b[:\s-]*([A-Za-z0-9/-]{4,})", desc, re.IGNORECASE)
    if m:
        return m.group(2)[:60]
    m2 = re.search(r"\b([A-Z]{2,6}-\d{2,})\b", desc)
    if m2:
        return m2.group(1)[:60]
    return None


def _looks_like_header(line: str) -> bool:
    l = (line or "").lower()
    has_txn = ("txn" in l and "date" in l) or ("transaction" in l and "date" in l)
    has_value = "value" in l and "date" in l
    has_desc = "description" in l or "narration" in l or "particular" in l
    has_debit = "debit" in l or "dr" in l
    has_credit = "credit" in l or "cr" in l
    has_balance = "balance" in l
    return has_txn and has_desc and (has_debit or has_credit) and (has_value or has_balance)


def _split_columns(line: str) -> list[str]:
    # pypdf text extraction often separates table columns with multiple spaces.
    cols = [c.strip() for c in re.split(r"\s{2,}", (line or "").strip()) if c.strip()]
    if cols:
        return cols
    return [c for c in (line or "").strip().split(" ") if c]


def _parse_amount_field(value: str) -> Optional[Decimal]:
    raw = (value or "").strip()
    if not raw:
        return None
    # drop trailing CR/DR if present in a table column
    raw = re.sub(r"\b(CR|DR)\b$", "", raw, flags=re.IGNORECASE).strip()
    if not raw:
        return None
    if not _AMOUNT_TOKEN_RE.match(raw):
        return None
    return abs(_parse_amount_token(raw))


def _row_from_table_line(line: str) -> Optional[ParsedStatementRow]:
    cols = _split_columns(line)
    if len(cols) < 4:
        return None

    if not _DATE_RE.match(cols[0]):
        return None

    txn_date = _parse_date(cols[0])
    idx = 1
    value_date: Optional[date] = None
    if idx < len(cols) and _DATE_RE.match(cols[idx]):
        try:
            value_date = _parse_date(cols[idx])
            idx += 1
        except Exception:
            value_date = None

    # Parse trailing numeric columns (often debit/credit/balance). We take up to 3 amounts from the right.
    trailing_amounts: list[Optional[Decimal]] = []
    trailing_count = 0
    for c in reversed(cols[idx:]):
        amt = _parse_amount_field(c)
        if amt is None:
            break
        trailing_amounts.append(amt)
        trailing_count += 1
        if trailing_count >= 3:
            break

    trailing_amounts = list(reversed(trailing_amounts))
    middle_end = len(cols) - trailing_count
    desc_parts = cols[idx:middle_end]
    description = _collapse_spaces(" ".join(desc_parts)) or "Statement transaction"

    debit: Optional[Decimal] = None
    credit: Optional[Decimal] = None
    balance: Optional[Decimal] = None

    # Common ordering: Debit, Credit, Balance (3 amounts)
    if trailing_count == 3:
        debit, credit, balance = trailing_amounts[0], trailing_amounts[1], trailing_amounts[2]
    elif trailing_count == 2:
        # Often: Amount + Balance. Infer debit/credit from keywords.
        amount, balance = trailing_amounts[0], trailing_amounts[1]
        desc_upper = description.upper()
        looks_credit = "REFUND" in desc_upper or "REVERSAL" in desc_upper or "CASHBACK" in desc_upper or "CR" in desc_upper
        if looks_credit:
            credit = amount
        else:
            debit = amount
    elif trailing_count == 1:
        # Only amount present; treat as debit by default.
        debit = trailing_amounts[0]

    reference = _guess_reference(description)
    return ParsedStatementRow(
        transaction_date=txn_date,
        value_date=value_date,
        description=description,
        debit=debit,
        credit=credit,
        reference=reference,
        balance=balance,
    )


def _line_to_row(line: str) -> Optional[ParsedStatementRow]:
    # Heuristic: line begins with a date and ends with an amount token.
    dm = _DATE_RE.match(line)
    if not dm:
        return None
    am = _AMOUNT_RE.search(line)
    if not am:
        return None

    raw_date = dm.group("d")
    txn_date = _parse_date(raw_date)

    amt_token = am.group("a")
    amt = _parse_amount_token(amt_token)

    suffix = (am.group("suffix") or "").upper()
    content = line[len(dm.group(0)) : am.start()].strip(" -")
    content = _collapse_spaces(content)

    # Try to split optional value date if it appears right after txn date.
    value_date: Optional[date] = None
    if content:
        parts = content.split(" ", 1)
        if parts and _DATE_RE.match(parts[0]):
            try:
                value_date = _parse_date(parts[0])
                content = (parts[1] if len(parts) > 1 else "").strip()
            except Exception:
                value_date = None

    description = content or "Statement transaction"
    reference = _guess_reference(description)

    # Debit/credit inference:
    # - If suffix says CR, treat as credit; DR or empty -> debit.
    # - If description suggests refund/credit, treat as credit.
    debit: Optional[Decimal] = None
    credit: Optional[Decimal] = None
    desc_upper = description.upper()
    looks_credit = suffix == "CR" or "REFUND" in desc_upper or "REVERSAL" in desc_upper or "CASHBACK" in desc_upper
    if looks_credit:
        credit = abs(amt)
    else:
        debit = abs(amt)

    return ParsedStatementRow(
        transaction_date=txn_date,
        value_date=value_date,
        description=description,
        debit=debit,
        credit=credit,
        reference=reference,
        balance=None,
    )


def parse_credit_card_rows_from_text(full_text: str) -> list[ParsedStatementRow]:
    text = (full_text or "").strip()
    if not text:
        raise StatementParseError("No text to parse")

    lines = list(_iter_text_lines(text))
    if not lines:
        raise StatementParseError("No text to parse")

    # Prefer table parsing when we can detect a header line.
    header_idx: Optional[int] = None
    for i, ln in enumerate(lines[:200]):
        if _looks_like_header(ln):
            header_idx = i
            break

    rows: list[ParsedStatementRow] = []
    if header_idx is not None:
        for ln in lines[header_idx + 1 :]:
            # stop conditions (common footers)
            low = ln.lower()
            if low.startswith("total") or "statement summary" in low:
                continue
            r = _row_from_table_line(ln)
            if r:
                rows.append(r)

    # Fallback: generic "date ... amount" line parsing
    if not rows:
        for ln in lines:
            r = _line_to_row(ln)
            if r:
                rows.append(r)

    if not rows:
        raise StatementParseError(
            "Could not detect transaction lines in the PDF text. Try exporting a statement CSV, or share a sample PDF format to improve parsing."
        )

    return rows


def extract_credit_card_rows_from_pdf_bytes(content: bytes) -> list[ParsedStatementRow]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as e:  # pragma: no cover
        raise StatementParseError("PDF parsing is not installed (missing pypdf)") from e

    try:
        reader = PdfReader(io.BytesIO(content))
    except Exception as e:
        raise StatementParseError("Invalid PDF file") from e

    all_text_parts: list[str] = []
    for page in reader.pages:
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        if txt:
            all_text_parts.append(txt)

    full_text = "\n".join(all_text_parts).strip()
    if not full_text:
        raise StatementParseError(
            "No selectable text found in PDF. If this is a scanned statement, OCR support is not enabled on this server."
        )
    return parse_credit_card_rows_from_text(full_text)
