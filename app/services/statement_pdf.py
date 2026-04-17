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

    rows: list[ParsedStatementRow] = []
    for line in _iter_text_lines(full_text):
        row = _line_to_row(line)
        if row:
            rows.append(row)

    if not rows:
        raise StatementParseError(
            "Could not detect transaction lines in the PDF text. Try exporting a statement CSV, or share a sample PDF format to improve parsing."
        )

    return rows

