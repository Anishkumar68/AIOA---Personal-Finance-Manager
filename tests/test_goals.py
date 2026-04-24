"""Tests for goals (savings targets) functionality."""

import pytest
from datetime import date
from decimal import Decimal
from fastapi import status


class TestGoals:
    def test_create_goal_and_list_progress(self, authenticated_client):
        payload = {
            "name": "Vacation",
            "currency": "INR",
            "target_amount": "50000.00",
            "start_date": date.today().isoformat(),
            "target_date": None,
            "note": "Trip fund",
        }

        res = authenticated_client.post("/api/v1/goals/", json=payload)
        assert res.status_code == status.HTTP_201_CREATED
        created = res.json()
        assert created["name"] == "Vacation"
        assert created["currency"] == "INR"

        list_res = authenticated_client.get("/api/v1/goals/")
        assert list_res.status_code == status.HTTP_200_OK
        items = list_res.json()
        assert isinstance(items, list)
        assert len(items) == 1

        g = items[0]
        assert g["name"] == "Vacation"
        assert Decimal(str(g["saved_amount"])) == Decimal("0")
        assert Decimal(str(g["remaining_amount"])) == Decimal("50000.00")
        assert g["contributions_count"] == 0
        assert g["is_completed"] is False

    def test_add_contribution_updates_progress(self, authenticated_client):
        create_res = authenticated_client.post(
            "/api/v1/goals/",
            json={
                "name": "Emergency Fund",
                "currency": "INR",
                "target_amount": "1000.00",
                "start_date": date.today().isoformat(),
            },
        )
        assert create_res.status_code == status.HTTP_201_CREATED
        goal_id = create_res.json()["id"]

        contrib_res = authenticated_client.post(
            f"/api/v1/goals/{goal_id}/contributions",
            json={"amount": "250.00", "date": date.today().isoformat(), "note": "Saved"},
        )
        assert contrib_res.status_code == status.HTTP_201_CREATED
        contrib = contrib_res.json()
        assert contrib["goal_id"] == goal_id
        assert Decimal(str(contrib["amount"])) == Decimal("250.00")

        list_res = authenticated_client.get("/api/v1/goals/")
        g = list_res.json()[0]
        assert Decimal(str(g["saved_amount"])) == Decimal("250.00")
        assert Decimal(str(g["remaining_amount"])) == Decimal("750.00")
        assert g["contributions_count"] == 1
        assert g["progress_pct"] > 0

    def test_archived_goal_rejects_contributions(self, authenticated_client):
        create_res = authenticated_client.post(
            "/api/v1/goals/",
            json={
                "name": "New Phone",
                "currency": "INR",
                "target_amount": "2000.00",
                "start_date": date.today().isoformat(),
            },
        )
        goal_id = create_res.json()["id"]

        upd_res = authenticated_client.put(f"/api/v1/goals/{goal_id}", json={"is_active": False})
        assert upd_res.status_code == status.HTTP_200_OK
        assert upd_res.json()["is_active"] is False

        contrib_res = authenticated_client.post(
            f"/api/v1/goals/{goal_id}/contributions",
            json={"amount": "10.00", "date": date.today().isoformat()},
        )
        assert contrib_res.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_goal(self, authenticated_client):
        create_res = authenticated_client.post(
            "/api/v1/goals/",
            json={
                "name": "Short Goal",
                "currency": "INR",
                "target_amount": "100.00",
                "start_date": date.today().isoformat(),
            },
        )
        goal_id = create_res.json()["id"]

        del_res = authenticated_client.delete(f"/api/v1/goals/{goal_id}")
        assert del_res.status_code == status.HTTP_204_NO_CONTENT

        get_res = authenticated_client.get(f"/api/v1/goals/{goal_id}")
        assert get_res.status_code == status.HTTP_404_NOT_FOUND

