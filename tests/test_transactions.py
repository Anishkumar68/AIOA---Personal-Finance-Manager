"""Tests for transactions functionality."""

import pytest
from fastapi import status
from datetime import date
from decimal import Decimal


class TestTransactions:
    """Test transaction endpoints."""
    
    @pytest.fixture
    def test_account(self, authenticated_client):
        """Create a test account."""
        account_data = {
            "name": "Main Account",
            "type": "bank",
            "currency": "USD",
            "opening_balance": "5000.00"
        }
        response = authenticated_client.post("/api/v1/accounts/", json=account_data)
        return response.json()
    
    @pytest.fixture
    def test_category(self, authenticated_client):
        """Get a test category."""
        response = authenticated_client.get("/api/v1/categories/")
        categories = response.json()
        # Get an expense category
        expense_cats = [c for c in categories if c["type"] == "expense"]
        return expense_cats[0] if expense_cats else None
    
    def test_create_expense_transaction(self, authenticated_client, test_account, test_category):
        """Test creating an expense transaction."""
        if not test_category:
            pytest.skip("No expense category available")
        
        transaction_data = {
            "type": "expense",
            "amount": "50.00",
            "account_id": test_account["id"],
            "category_id": test_category["id"],
            "date": str(date.today()),
            "note": "Grocery shopping"
        }
        
        response = authenticated_client.post("/api/v1/transactions/", json=transaction_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["type"] == "expense"
        assert data["amount"] == "50.00"
    
    def test_create_income_transaction(self, authenticated_client, test_account):
        """Test creating an income transaction."""
        # Get income category
        response = authenticated_client.get("/api/v1/categories/")
        categories = response.json()
        income_cats = [c for c in categories if c["type"] == "income"]
        
        if not income_cats:
            pytest.skip("No income category available")
        
        transaction_data = {
            "type": "income",
            "amount": "2000.00",
            "account_id": test_account["id"],
            "category_id": income_cats[0]["id"],
            "date": str(date.today()),
            "note": "Salary"
        }
        
        response = authenticated_client.post("/api/v1/transactions/", json=transaction_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["type"] == "income"
        assert data["amount"] == "2000.00"
    
    def test_get_transactions(self, authenticated_client):
        """Test getting transactions."""
        response = authenticated_client.get("/api/v1/transactions/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data

    def test_transactions_amount_range_filter(self, authenticated_client, test_account, test_category):
        """Filter by min_amount/max_amount."""
        if not test_category:
            pytest.skip("No expense category available")

        # Create two expenses with different amounts
        for amt in ("10.00", "99.00"):
            resp = authenticated_client.post(
                "/api/v1/transactions/",
                json={
                    "type": "expense",
                    "amount": amt,
                    "account_id": test_account["id"],
                    "category_id": test_category["id"],
                    "date": str(date.today()),
                    "note": f"Amount {amt}",
                },
            )
            assert resp.status_code == status.HTTP_201_CREATED

        # Only the 99.00 should match min_amount=50
        res = authenticated_client.get("/api/v1/transactions/?min_amount=50")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["total"] == 1
        assert data["items"][0]["amount"] == "99.00"

    def test_export_transactions_csv(self, authenticated_client, test_account, test_category):
        """Test exporting transactions as CSV."""
        if not test_category:
            pytest.skip("No expense category available")

        # Ensure there is at least one transaction
        transaction_data = {
            "type": "expense",
            "amount": "12.34",
            "account_id": test_account["id"],
            "category_id": test_category["id"],
            "date": str(date.today()),
            "note": "Export test"
        }
        create_response = authenticated_client.post("/api/v1/transactions/", json=transaction_data)
        assert create_response.status_code == status.HTTP_201_CREATED

        response = authenticated_client.get("/api/v1/transactions/export")
        assert response.status_code == status.HTTP_200_OK
        assert "text/csv" in response.headers.get("content-type", "")
        body = response.text
        assert "Date" in body
        assert "Amount" in body

    def test_import_transactions_csv_partial(self, authenticated_client, test_account, test_category):
        """Test importing transactions from CSV."""
        if not test_category:
            pytest.skip("No expense category available")

        csv_body = (
            "Date,Type,Amount,Account ID,Category ID,Note,Reference\n"
            f"{date.today().isoformat()},expense,10.00,{test_account['id']},{test_category['id']},Imported row,REF-1\n"
        )

        response = authenticated_client.post(
            "/api/v1/transactions/import?mode=partial",
            files={"file": ("transactions.csv", csv_body, "text/csv")}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["imported"] == 1
        assert data["failed"] == 0
        assert data["total_rows"] == 1

        # Verify account balance changed
        acc_res = authenticated_client.get("/api/v1/accounts/")
        assert acc_res.status_code == status.HTTP_200_OK
        accounts = acc_res.json()
        acc = next(a for a in accounts if a["id"] == test_account["id"])
        assert Decimal(acc["current_balance"]) == Decimal("4990.00")

    def test_import_transactions_csv_bank_statement_default_account(self, authenticated_client, test_account):
        """Bank-export-like CSV should import with default_account_id + Debit/Credit columns."""
        csv_body = (
            "Transaction Date,Value Date,Description/Narration,Cheque/ Reference No.,Debit (INR),Credit (INR),Balance (INR)\n"
            f"{date.today().isoformat()},{date.today().isoformat()},Imported bank row,REF-1,10.00,,4990.00\n"
        )

        response = authenticated_client.post(
            f"/api/v1/transactions/import?mode=partial&default_account_id={test_account['id']}",
            files={"file": ("bank.csv", csv_body, "text/csv")},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["imported"] == 1
        assert data["failed"] == 0
        assert data["total_rows"] == 1

        acc_res = authenticated_client.get("/api/v1/accounts/")
        assert acc_res.status_code == status.HTTP_200_OK
        accounts = acc_res.json()
        acc = next(a for a in accounts if a["id"] == test_account["id"])
        assert Decimal(acc["current_balance"]) == Decimal("4990.00")

    def test_import_transactions_csv_dry_run(self, authenticated_client, test_account, test_category):
        """Dry-run import should not create records."""
        if not test_category:
            pytest.skip("No expense category available")

        csv_body = (
            "Date,Type,Amount,Account ID,Category ID,Note\n"
            f"{date.today().isoformat()},expense,5.00,{test_account['id']},{test_category['id']},Dry run row\n"
        )

        response = authenticated_client.post(
            "/api/v1/transactions/import?mode=partial&dry_run=true",
            files={"file": ("transactions.csv", csv_body, "text/csv")}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["dry_run"] is True
        assert data["imported"] == 1
        assert data["failed"] == 0

        # No transaction should be created in dry-run
        tx_res = authenticated_client.get("/api/v1/transactions/")
        assert tx_res.status_code == status.HTTP_200_OK
        assert tx_res.json()["total"] == 0
    
    def test_delete_transaction(self, authenticated_client, test_account, test_category):
        """Test deleting a transaction."""
        if not test_category:
            pytest.skip("No expense category available")
        
        # Create a transaction first
        transaction_data = {
            "type": "expense",
            "amount": "25.00",
            "account_id": test_account["id"],
            "category_id": test_category["id"],
            "date": str(date.today()),
            "note": "Test transaction"
        }
        create_response = authenticated_client.post("/api/v1/transactions/", json=transaction_data)
        transaction_id = create_response.json()["id"]
        
        # Delete it
        response = authenticated_client.delete(f"/api/v1/transactions/{transaction_id}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
