"""Transaction API routes."""

from typing import Optional, Dict, List
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from fastapi.responses import StreamingResponse
import io
import csv

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.category import Category
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionFilters,
    TransactionImportResponse,
    TransactionImportRowError,
)
from app.services import transaction_service
from app.services.statement_pdf import StatementParseError, extract_credit_card_rows_from_pdf_bytes

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/", response_model=dict)
def get_transactions(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    account_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get transactions with filters and pagination."""
    filters = TransactionFilters(
        from_date=from_date,
        to_date=to_date,
        account_id=account_id,
        category_id=category_id,
        type=type,
        search=search,
        page=page,
        limit=limit
    )
    
    transactions, total = transaction_service.get_transactions(db, current_user.id, filters)
    
    return {
        "items": transactions,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 0
    }


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new transaction."""
    return transaction_service.create_transaction(db, current_user.id, transaction_data)


@router.get("/export")
def export_transactions(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    account_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Export transactions as CSV file."""
    query = (
        db.query(Transaction)
        .options(
            joinedload(Transaction.account),
            joinedload(Transaction.category),
            joinedload(Transaction.transfer_account),
        )
        .filter(Transaction.user_id == current_user.id)
    )

    if from_date:
        query = query.filter(Transaction.date >= from_date)
    if to_date:
        query = query.filter(Transaction.date <= to_date)
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if type:
        query = query.filter(Transaction.type == type)
    if search:
        query = query.filter(Transaction.note.ilike(f"%{search}%"))

    query = query.order_by(Transaction.date.desc(), Transaction.created_at.desc())

    def iter_csv_rows():
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(
            [
                "ID",
                "Date",
                "Type",
                "Amount",
                "Account ID",
                "Account",
                "Category ID",
                "Category",
                "Note",
                "Reference",
                "Transfer Account ID",
                "Transfer Account",
                "Created At",
            ]
        )
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        for txn in query.yield_per(1000):
            writer.writerow(
                [
                    txn.id,
                    txn.date.isoformat(),
                    txn.type,
                    str(txn.amount),
                    txn.account_id,
                    txn.account.name if txn.account else "",
                    txn.category_id or "",
                    txn.category.name if txn.category else "",
                    txn.note or "",
                    txn.reference or "",
                    txn.transfer_account_id or "",
                    txn.transfer_account.name if txn.transfer_account else "",
                    txn.created_at.isoformat() if txn.created_at else "",
                ]
            )
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    return StreamingResponse(
        iter_csv_rows(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )


@router.get("/import-template")
def import_template():
    """Download a CSV template for bulk transaction import."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Transaction Date",
            "Value Date",
            "Description/Narration",
            "Cheque/ Reference No.",
            "Debit (INR)",
            "Credit (INR)",
            "Balance (INR)",
        ]
    )
    writer.writerow(["2026-01-15", "2026-01-15", "Grocery shopping", "INV-123", "250.00", "", "4750.00"])
    writer.writerow(["2026-01-20", "2026-01-20", "Salary credit", "NEFT-456", "", "2000.00", "6750.00"])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions-import-template.csv"},
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific transaction."""
    return transaction_service.get_transaction(db, transaction_id, current_user.id)


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a transaction."""
    return transaction_service.update_transaction(db, transaction_id, current_user.id, transaction_data)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a transaction."""
    transaction_service.delete_transaction(db, transaction_id, current_user.id)
    return None


def _norm_header(value: str) -> str:
    raw = (value or "").strip().lower()
    raw = raw.replace("\ufeff", "")
    raw = re.sub(r"[^a-z0-9]+", "_", raw)
    return raw.strip("_")


def _get_first(normalized: Dict[str, Optional[str]], *keys: str) -> str:
    for k in keys:
        v = normalized.get(k)
        if v is None:
            continue
        if isinstance(v, str) and v.strip():
            return v.strip()
        if not isinstance(v, str) and v:
            return str(v).strip()
    return ""


def _parse_date(value: str) -> date:
    raw = (value or "").strip()
    if not raw:
        raise ValueError("Missing date")
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError("Invalid date format (expected YYYY-MM-DD or DD/MM/YYYY)")


def _parse_amount(value: str) -> Decimal:
    raw = (value or "").strip()
    if not raw:
        raise ValueError("Missing amount")
    cleaned = raw.replace(",", "")
    cleaned = cleaned.replace("₹", "").replace("$", "").replace("€", "").replace("£", "").strip()
    try:
        amount = Decimal(cleaned)
    except (InvalidOperation, ValueError):
        raise ValueError("Invalid amount")
    if amount <= 0:
        raise ValueError("Amount must be > 0")
    return amount


def _parse_type(value: str) -> str:
    raw = (value or "").strip().lower()
    mapping = {
        "income": "income",
        "expense": "expense",
        "transfer": "transfer",
        "credit": "income",
        "debit": "expense",
        "cr": "income",
        "dr": "expense",
    }
    if raw in mapping:
        return mapping[raw]
    raise ValueError("Invalid type (expected income/expense/transfer)")


@router.post("/import", response_model=TransactionImportResponse)
async def import_transactions(
    file: UploadFile = File(...),
    mode: str = Query("partial", description="partial | all_or_nothing"),
    dry_run: bool = Query(False),
    default_account_id: Optional[int] = Query(None, description="Used when CSV omits Account/Account ID columns"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Import transactions from a CSV file."""
    return await _import_transactions_any(
        file=file,
        mode=mode,
        dry_run=dry_run,
        default_account_id=default_account_id,
        current_user=current_user,
        db=db,
        kind="csv",
    )


@router.post("/import-pdf", response_model=TransactionImportResponse)
async def import_transactions_pdf(
    file: UploadFile = File(...),
    mode: str = Query("partial", description="partial | all_or_nothing"),
    dry_run: bool = Query(False),
    default_account_id: Optional[int] = Query(None, description="Account to apply to all parsed rows"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Import transactions from a credit-card statement PDF (text-based PDFs supported)."""
    if default_account_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="default_account_id is required for PDF import")
    return await _import_transactions_any(
        file=file,
        mode=mode,
        dry_run=dry_run,
        default_account_id=default_account_id,
        current_user=current_user,
        db=db,
        kind="pdf",
    )


async def _import_transactions_any(
    *,
    file: UploadFile,
    mode: str,
    dry_run: bool,
    default_account_id: Optional[int],
    current_user: User,
    db: Session,
    kind: str,
) -> TransactionImportResponse:
    if mode not in {"partial", "all_or_nothing"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid mode")

    content = await file.read()
    if kind == "csv":
        if not file.filename or not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please upload a .csv file")

        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV must be UTF-8 encoded")

        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV header row is missing")
    elif kind == "pdf":
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please upload a .pdf file")
        try:
            rows = extract_credit_card_rows_from_pdf_bytes(content)
        except StatementParseError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Transaction Date",
                "Value Date",
                "Description/Narration",
                "Cheque/ Reference No.",
                "Debit (INR)",
                "Credit (INR)",
                "Balance (INR)",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r.transaction_date.isoformat(),
                    (r.value_date.isoformat() if r.value_date else ""),
                    r.description,
                    r.reference or "",
                    (str(r.debit) if r.debit is not None else ""),
                    (str(r.credit) if r.credit is not None else ""),
                    (str(r.balance) if r.balance is not None else ""),
                ]
            )
        output.seek(0)
        reader = csv.DictReader(io.StringIO(output.getvalue()))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid import kind")

    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    categories = db.query(Category).filter(Category.user_id == current_user.id).all()

    accounts_by_name: Dict[str, List[Account]] = {}
    for acc in accounts:
        accounts_by_name.setdefault(acc.name.strip().lower(), []).append(acc)

    categories_by_name: Dict[str, List[Category]] = {}
    for cat in categories:
        categories_by_name.setdefault(cat.name.strip().lower(), []).append(cat)

    if default_account_id is not None:
        default_acc = (
            db.query(Account)
            .filter(Account.id == default_account_id, Account.user_id == current_user.id)
            .first()
        )
        if not default_acc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="default_account_id is invalid")

    def resolve_account_id(account_value: str) -> int:
        if not account_value:
            raise ValueError("Missing account")
        key = account_value.strip().lower()
        matches = accounts_by_name.get(key, [])
        if not matches:
            raise ValueError(f"Account not found: {account_value}")
        if len(matches) > 1:
            raise ValueError(f"Ambiguous account name: {account_value}")
        return matches[0].id

    def resolve_category_id(category_value: str, txn_type: str) -> int:
        if not category_value:
            raise ValueError("Missing category")
        key = category_value.strip().lower()
        matches = categories_by_name.get(key, [])
        if not matches:
            raise ValueError(f"Category not found: {category_value}")
        if len(matches) == 1:
            return matches[0].id
        typed = [c for c in matches if c.type == txn_type]
        if len(typed) == 1:
            return typed[0].id
        raise ValueError(f"Ambiguous category name: {category_value}")

    total_rows = 0
    imported = 0
    failed = 0
    errors: List[TransactionImportRowError] = []
    to_create: List[tuple[int, TransactionCreate, Dict[str, Optional[str]]]] = []

    for row in reader:
        total_rows += 1
        line_num = reader.line_num or (total_rows + 1)
        raw_row = {k: (str(v).strip() if isinstance(v, str) else (str(v) if v is not None else None)) for k, v in (row or {}).items() if k}
        normalized = {_norm_header(k): (v.strip() if isinstance(v, str) else v) for k, v in (row or {}).items() if k}

        try:
            raw_type = _get_first(normalized, "type", "dr_cr", "drcr", "transaction_type")
            raw_amount = _get_first(normalized, "amount")
            raw_debit = _get_first(
                normalized,
                "debit_inr",
                "debit",
                "withdrawal_amount",
                "withdrawal",
            )
            raw_credit = _get_first(
                normalized,
                "credit_inr",
                "credit",
                "deposit_amount",
                "deposit",
            )

            txn_type = _parse_type(raw_type) if raw_type else ""
            if not raw_amount and (raw_debit or raw_credit):
                if raw_debit and raw_credit:
                    raise ValueError("Provide only one of Debit/Credit")
                if raw_debit:
                    txn_type = "expense"
                    raw_amount = raw_debit
                else:
                    txn_type = "income"
                    raw_amount = raw_credit
            if not txn_type:
                raise ValueError("Missing type")

            txn_date_raw = _get_first(normalized, "transaction_date", "date", "value_date")
            txn_date = _parse_date(txn_date_raw)
            amount = _parse_amount(raw_amount)

            raw_account_id = normalized.get("account_id") or normalized.get("accountid")
            raw_account = _get_first(normalized, "account")
            if raw_account_id:
                account_id_val = int(str(raw_account_id).strip())
            elif raw_account:
                account_id_val = resolve_account_id(raw_account)
            elif default_account_id is not None:
                account_id_val = default_account_id
            else:
                raise ValueError("Missing account")

            raw_transfer_account_id = normalized.get("transfer_account_id") or normalized.get("transfer_accountid")
            raw_transfer_account = normalized.get("transfer_account", "") or normalized.get("transferaccount", "")
            transfer_account_id_val: Optional[int] = None
            if raw_transfer_account_id:
                transfer_account_id_val = int(str(raw_transfer_account_id).strip())
            elif raw_transfer_account:
                transfer_account_id_val = resolve_account_id(raw_transfer_account)
            if txn_type == "transfer" and not transfer_account_id_val:
                raise ValueError("Transfer requires transfer account")

            raw_category_id = normalized.get("category_id") or normalized.get("categoryid")
            raw_category = normalized.get("category", "")
            category_id_val: Optional[int] = None
            if txn_type in {"income", "expense"}:
                if raw_category_id:
                    category_id_val = int(str(raw_category_id).strip())
                elif raw_category:
                    category_id_val = resolve_category_id(raw_category, txn_type)

            description = _get_first(normalized, "description_narration", "description", "narration", "particulars")
            note = _get_first(normalized, "note") or description or None
            value_date = _get_first(normalized, "value_date")
            if note and value_date and value_date not in note:
                note = f"{note} (Value Date: {value_date})"

            reference = _get_first(normalized, "cheque_reference_no", "reference") or None

            txn = TransactionCreate(
                type=txn_type,
                amount=amount,
                account_id=account_id_val,
                category_id=category_id_val,
                date=txn_date,
                note=note,
                reference=reference,
                transfer_account_id=transfer_account_id_val,
            )
            to_create.append((line_num, txn, raw_row))
        except Exception as e:
            failed += 1
            errors.append(
                TransactionImportRowError(
                    row_number=line_num,
                    message=str(e),
                    raw=raw_row,
                )
            )

    if dry_run:
        return TransactionImportResponse(
            total_rows=total_rows,
            imported=len(to_create),
            failed=failed,
            skipped=0,
            dry_run=True,
            mode=mode,
            errors=errors,
        )

    if mode == "all_or_nothing" and errors:
        return TransactionImportResponse(
            total_rows=total_rows,
            imported=0,
            failed=failed,
            skipped=0,
            dry_run=False,
            mode=mode,
            errors=errors,
        )

    if mode == "all_or_nothing":
        try:
            for _, txn, _ in to_create:
                transaction_service.create_transaction(db, current_user.id, txn, commit=False)
            db.commit()
            imported = len(to_create)
        except HTTPException as e:
            db.rollback()
            raise HTTPException(status_code=e.status_code, detail=e.detail)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        return TransactionImportResponse(
            total_rows=total_rows,
            imported=imported,
            failed=failed,
            skipped=0,
            dry_run=False,
            mode=mode,
            errors=errors,
        )

    # partial
    for line_num, txn, raw_row in to_create:
        try:
            transaction_service.create_transaction(db, current_user.id, txn)
            imported += 1
        except HTTPException as e:
            failed += 1
            errors.append(
                TransactionImportRowError(
                    row_number=line_num,
                    message=str(e.detail),
                    raw=raw_row,
                )
            )
        except Exception as e:
            failed += 1
            errors.append(TransactionImportRowError(row_number=line_num, message=str(e), raw=raw_row))

    return TransactionImportResponse(
        total_rows=total_rows,
        imported=imported,
        failed=failed,
        skipped=0,
        dry_run=False,
        mode=mode,
        errors=errors,
    )
