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
