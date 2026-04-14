"""Tests for accounts functionality."""

import pytest
from fastapi import status
from decimal import Decimal


class TestAccounts:
    """Test account endpoints."""
    
    def test_create_account(self, authenticated_client):
        """Test creating an account."""
        account_data = {
            "name": "Cash Wallet",
            "type": "cash",
            "currency": "USD",
            "opening_balance": "1000.00"
        }
        
        response = authenticated_client.post("/api/v1/accounts/", json=account_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == account_data["name"]
        assert data["type"] == account_data["type"]
        assert data["current_balance"] == "1000.00"
    
    def test_get_accounts(self, authenticated_client):
        """Test getting all accounts."""
        # Create an account first
        account_data = {
            "name": "Bank Account",
            "type": "bank",
            "currency": "USD",
            "opening_balance": "5000.00"
        }
        authenticated_client.post("/api/v1/accounts/", json=account_data)
        
        response = authenticated_client.get("/api/v1/accounts/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
    
    def test_get_account(self, authenticated_client):
        """Test getting a specific account."""
        # Create an account first
        account_data = {
            "name": "Savings",
            "type": "bank",
            "currency": "USD",
            "opening_balance": "10000.00"
        }
        create_response = authenticated_client.post("/api/v1/accounts/", json=account_data)
        account_id = create_response.json()["id"]
        
        response = authenticated_client.get(f"/api/v1/accounts/{account_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == account_id
        assert data["name"] == account_data["name"]
    
    def test_update_account(self, authenticated_client):
        """Test updating an account."""
        # Create an account first
        account_data = {
            "name": "Old Name",
            "type": "cash",
            "currency": "USD",
            "opening_balance": "100.00"
        }
        create_response = authenticated_client.post("/api/v1/accounts/", json=account_data)
        account_id = create_response.json()["id"]
        
        # Update it
        update_data = {"name": "New Name"}
        response = authenticated_client.put(
            f"/api/v1/accounts/{account_id}",
            json=update_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "New Name"
    
    def test_delete_account(self, authenticated_client):
        """Test deleting an account."""
        # Create an account first
        account_data = {
            "name": "To Delete",
            "type": "wallet",
            "currency": "USD",
            "opening_balance": "50.00"
        }
        create_response = authenticated_client.post("/api/v1/accounts/", json=account_data)
        account_id = create_response.json()["id"]
        
        # Delete it
        response = authenticated_client.delete(f"/api/v1/accounts/{account_id}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
