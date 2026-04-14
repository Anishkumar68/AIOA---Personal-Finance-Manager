"""Tests for authentication functionality."""

import pytest
from fastapi import status


class TestAuth:
    """Test authentication endpoints."""
    
    def test_register_user(self, client, test_user_data):
        """Test user registration."""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == test_user_data["name"]
        assert data["email"] == test_user_data["email"]
        assert "id" in data
        assert data["is_active"] is True
    
    def test_register_duplicate_email(self, client, test_user_data):
        """Test registering with duplicate email."""
        # First registration
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Second registration with same email
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_login_success(self, client, test_user_data):
        """Test successful login."""
        # Register first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client, test_user_data):
        """Test login with wrong password."""
        # Register first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["email"],
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user(self, authenticated_client):
        """Test getting current user."""
        response = authenticated_client.get("/api/v1/auth/me")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "email" in data
