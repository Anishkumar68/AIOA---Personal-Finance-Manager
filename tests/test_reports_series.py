"""Tests for report series endpoints used by charts."""

from datetime import date
from fastapi import status


class TestReportSeries:
    def test_cashflow_series_day_bucket(self, authenticated_client, test_user_data):
        # Create account
        acc = authenticated_client.post(
            "/api/v1/accounts/",
            json={"name": "A", "type": "bank", "currency": "INR", "opening_balance": "0.00"},
        )
        assert acc.status_code == status.HTTP_201_CREATED
        account_id = acc.json()["id"]

        # Get an income and expense category
        cats = authenticated_client.get("/api/v1/categories/").json()
        income_cat = next(c for c in cats if c["type"] == "income")
        expense_cat = next(c for c in cats if c["type"] == "expense")

        today = date.today().isoformat()
        # Create income + expense
        r1 = authenticated_client.post(
            "/api/v1/transactions/",
            json={
                "type": "income",
                "amount": "100.00",
                "account_id": account_id,
                "category_id": income_cat["id"],
                "date": today,
                "note": "salary",
            },
        )
        assert r1.status_code == status.HTTP_201_CREATED

        r2 = authenticated_client.post(
            "/api/v1/transactions/",
            json={
                "type": "expense",
                "amount": "25.00",
                "account_id": account_id,
                "category_id": expense_cat["id"],
                "date": today,
                "note": "food",
            },
        )
        assert r2.status_code == status.HTTP_201_CREATED

        res = authenticated_client.get(
            f"/api/v1/reports/cashflow-series?from_date={today}&to_date={today}&bucket=day"
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["bucket"] == "day"
        assert len(data["series"]) == 1
        assert data["series"][0]["income"] == "100.00"
        assert data["series"][0]["expense"] == "25.00"
        assert data["series"][0]["net"] == "75.00"

