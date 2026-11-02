def test_list_claims(client):
    claims = client.get("/api/claims").json()
    assert [claim["claim_id"] for claim in claims] == [
        f"CLM-{n}" for n in range(1001, 1026)
    ]
    assert {claim["status"] for claim in claims} == {"waiting"}
    assert claims[0] == {
        "claim_id": "CLM-1001",
        "customer_name": "Maya Patel",
        "claim_type": "trip_delay",
        "summary": "Flight home canceled by the airline, rebooked the next morning",
        "submitted_on": "2026-06-24",
        "amount_claimed": 420.0,
        "status": "waiting",
        "decision": None,
        "payout": None,
    }


def test_get_claim(client):
    claim = client.get("/api/claims/CLM-1001").json()
    assert claim["customer_name"] == "Maya Patel"
    assert claim["story"].startswith("My flight home from Rome")
    assert sum(item["amount"] for item in claim["items"]) == 420.0
    assert len(claim["documents"]) == 4
    assert claim["status"] == "waiting"
    assert claim["thread_id"] is None
    assert claim["decision"] is None
    assert claim["payment"] is None


def test_unknown_records(client):
    for path, detail in [
        ("/api/claims/CLM-9999", "Claim CLM-9999 not found"),
        ("/api/policies/POL-9999", "Policy POL-9999 not found"),
        ("/api/customers/CUS-9999/history", "Customer CUS-9999 not found"),
    ]:
        response = client.get(path)
        assert response.status_code == 404
        assert response.json() == {"detail": detail}


def test_get_policy(client):
    policy = client.get("/api/policies/POL-2001").json()
    assert policy["plan"] == "premium"
    assert policy["plan_details"]["trip_delay_max"] == 800.0
    assert policy["plan_details"]["deductible"] == 50.0
    assert policy["add_ons"] == []
    assert policy["add_on_details"] == []
    assert policy["trip"]["destination"] == "Rome, Italy"


def test_get_policy_with_add_ons(client):
    policies = [client.get(f"/api/policies/POL-{n}").json() for n in range(2001, 2026)]
    with_electronics = [p for p in policies if "electronics_plus" in p["add_ons"]]
    assert with_electronics
    details = with_electronics[0]["add_on_details"]
    assert details[0]["electronics_per_item_limit"] == 1200.0


def test_get_claim_history(client):
    history = client.get("/api/customers/CUS-3001/history").json()
    assert history["name"] == "Maya Patel"
    assert [c["claim_id"] for c in history["previous_claims"]] == ["CLM-0412"]
    for personal in ["email", "phone", "address", "date_of_birth"]:
        assert personal not in history


def test_get_policy_wording(client):
    wording = client.get("/api/policy-wording").json()
    assert wording["version"] == "2026.1"
    assert wording["text"].startswith("# UnderCover Travel Insurance: Policy Wording")
