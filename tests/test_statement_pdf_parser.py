from datetime import date
from decimal import Decimal

import pytest

from app.services.statement_pdf import parse_credit_card_rows_from_text


def test_parse_table_like_text_with_debit_credit_balance():
    text = """
    Txn Date      Value Date    Description/Narration                 Debit        Credit       Balance
    15/01/2026    15/01/2026    AMAZON SELLER SERVICES               250.00                    4,750.00
    20/01/2026    20/01/2026    SALARY CREDIT                                   2,000.00      6,750.00
    """
    rows = parse_credit_card_rows_from_text(text)
    assert len(rows) == 2

    assert rows[0].transaction_date == date(2026, 1, 15)
    assert rows[0].value_date == date(2026, 1, 15)
    assert rows[0].debit == Decimal("250.00")
    assert rows[0].credit is None
    assert rows[0].balance == Decimal("4750.00")

    assert rows[1].transaction_date == date(2026, 1, 20)
    assert rows[1].value_date == date(2026, 1, 20)
    assert rows[1].debit is None
    assert rows[1].credit == Decimal("2000.00")
    assert rows[1].balance == Decimal("6750.00")


def test_parse_fallback_date_amount_lines():
    text = """
    2026-01-15 Grocery shopping 250.00
    2026-01-20 Salary credit 2000.00 CR
    """
    rows = parse_credit_card_rows_from_text(text)
    assert len(rows) == 2
    assert rows[0].transaction_date == date(2026, 1, 15)
    assert rows[0].debit == Decimal("250.00")
    assert rows[1].credit == Decimal("2000.00")

