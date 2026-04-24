"""Tests for password reset flow."""

from fastapi import status

from app.core.config import settings


class TestPasswordReset:
    def test_forgot_and_reset_password(self, client, test_user_data):
        # Register user
        reg = client.post("/api/v1/auth/register", json=test_user_data)
        assert reg.status_code == status.HTTP_200_OK

        # Enable DEBUG so API returns token for tests/local dev
        prev_debug = settings.DEBUG
        settings.DEBUG = True
        try:
            fp = client.post("/api/v1/auth/forgot-password", json={"email": test_user_data["email"]})
            assert fp.status_code == status.HTTP_200_OK
            data = fp.json()
            assert "message" in data
            assert data.get("reset_token")
            token = data["reset_token"]

            rp = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": "newpassword123"})
            assert rp.status_code == status.HTTP_200_OK

            # Login with new password works
            login = client.post("/api/v1/auth/login", json={"email": test_user_data["email"], "password": "newpassword123"})
            assert login.status_code == status.HTTP_200_OK
            assert login.json().get("access_token")
        finally:
            settings.DEBUG = prev_debug

