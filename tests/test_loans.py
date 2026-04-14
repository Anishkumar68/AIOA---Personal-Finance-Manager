"""Tests for Udhar Khata (contacts + loans) APIs."""


def test_contacts_and_loans_flow(authenticated_client):
    client = authenticated_client

    # Create a contact
    contact_res = client.post("/api/v1/contacts/", json={"name": "Ravi", "phone": "9999999999"})
    assert contact_res.status_code == 201
    contact = contact_res.json()
    assert contact["name"] == "Ravi"

    # Create a loan (money lent)
    loan_res = client.post(
        "/api/v1/loans/",
        json={
            "contact_id": contact["id"],
            "direction": "lent",
            "title": "Udhar",
            "currency": "INR",
            "start_date": "2026-04-13",
            "initial_amount": "1000",
            "initial_note": "Given in cash",
        },
    )
    assert loan_res.status_code == 201
    loan = loan_res.json()
    assert loan["direction"] == "lent"
    assert loan["contact_name"] == "Ravi"
    assert str(loan["total_disbursed"]) == "1000.00"
    assert str(loan["total_repaid"]) == "0.00"
    assert str(loan["outstanding"]) == "1000.00"

    # Add a repayment entry
    entry_res = client.post(
        f"/api/v1/loans/{loan['id']}/entries",
        json={"kind": "repayment", "amount": "200", "note": "Recovered"},
    )
    assert entry_res.status_code == 201
    entry = entry_res.json()
    assert entry["kind"] == "repayment"

    # Fetch loan details
    loan_detail_res = client.get(f"/api/v1/loans/{loan['id']}")
    assert loan_detail_res.status_code == 200
    loan_detail = loan_detail_res.json()
    assert str(loan_detail["total_disbursed"]) == "1000.00"
    assert str(loan_detail["total_repaid"]) == "200.00"
    assert str(loan_detail["outstanding"]) == "800.00"
    assert len(loan_detail["entries"]) == 2

    # List loans with filter
    list_res = client.get("/api/v1/loans/?direction=lent")
    assert list_res.status_code == 200
    payload = list_res.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == loan["id"]

