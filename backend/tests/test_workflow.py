import json

from backend import db


def start(client, claim_id="CLM-1001", thread_id="thread-1"):
    return client.post(f"/api/claims/{claim_id}/start", json={"thread_id": thread_id})


def decide(client, decision="approve", payout=420.0, claim_id="CLM-1001"):
    return client.post(
        f"/api/claims/{claim_id}/decision",
        json={
            "decision": decision,
            "payout": payout,
            "reasons": "The delay was covered.",
            "policy_section": "Section 3, Trip Delay",
        },
    )


def pay(client, amount, claim_id="CLM-1001"):
    return client.post(f"/api/claims/{claim_id}/payment", json={"amount": amount})


def sign_off(client, handler_id="HND-01", claim_id="CLM-1001"):
    return client.post(
        f"/api/claims/{claim_id}/sign-off", json={"handler_id": handler_id}
    )


def add_step(client, title, claim_id="CLM-1001"):
    return client.post(
        f"/api/claims/{claim_id}/steps",
        json={"kind": "tool", "title": title, "detail": "{}"},
    )


def test_start_claim(client):
    state = start(client).json()
    assert state["status"] == "in_progress"
    assert state["thread_id"] == "thread-1"
    assert state["decision"] is None


def test_restart_clears_steps(client):
    start(client)
    add_step(client, "Reading the claim")
    restarted = start(client, thread_id="thread-2").json()
    assert restarted["thread_id"] == "thread-2"
    assert client.get("/api/claims/CLM-1001/steps").json() == []


def test_cannot_start_a_decided_claim(client):
    start(client)
    decide(client)
    response = start(client)
    assert response.status_code == 409
    assert response.json() == {"detail": "CLM-1001 already has a decision"}


def test_start_unknown_claim(client):
    assert start(client, claim_id="CLM-9999").status_code == 404


def test_steps_in_order(client):
    start(client)
    first = add_step(client, "Reading the claim").json()
    add_step(client, "Reading the policy")
    steps = client.get("/api/claims/CLM-1001/steps").json()
    assert [step["title"] for step in steps] == [
        "Reading the claim",
        "Reading the policy",
    ]
    assert first["kind"] == "tool"
    assert first["created_at"]


def test_step_needs_a_title_and_a_claim(client):
    assert add_step(client, "").status_code == 422
    assert add_step(client, "Reading", claim_id="CLM-9999").status_code == 404
    assert client.get("/api/claims/CLM-9999/steps").status_code == 404


def test_decision_needs_a_claim_in_progress(client):
    response = decide(client)
    assert response.status_code == 409
    assert response.json() == {"detail": "CLM-1001 is not in progress"}


def test_approve_within_limit_is_decided(client):
    start(client)
    state = decide(client, payout=420).json()
    assert state["status"] == "decided"
    assert state["decision"]["decision"] == "approve"
    assert state["decision"]["payout"] == 420.0
    assert state["decision"]["policy_section"] == "Section 3, Trip Delay"
    claim = client.get("/api/claims/CLM-1001").json()
    assert claim["decision"]["reasons"] == "The delay was covered."
    queue = client.get("/api/claims").json()
    assert (queue[0]["decision"], queue[0]["payout"]) == ("approve", 420.0)


def test_approve_over_limit_waits_for_sign_off(client):
    start(client)
    assert decide(client, payout=1000.01).json()["status"] == "waiting_for_sign_off"


def test_decline_and_refer_pay_nothing(client):
    start(client)
    assert decide(client, "decline", 50).status_code == 422
    assert decide(client, "refer", 0).json()["status"] == "decided"
    start(client, claim_id="CLM-1002")
    declined = decide(client, "decline", 0, claim_id="CLM-1002").json()
    assert declined["decision"]["payout"] == 0


def test_decision_input_is_checked(client):
    start(client)
    assert decide(client, "approve", 0).status_code == 422
    assert decide(client, "approve", -5).status_code == 422
    assert decide(client, "maybe", 0).status_code == 422
    response = client.post(
        "/api/claims/CLM-1001/decision",
        json={
            "decision": "refer",
            "payout": 0,
            "reasons": "",
            "policy_section": "",
        },
    )
    assert response.status_code == 422


def test_amounts_round_to_the_cent(client):
    start(client)
    assert decide(client, payout=420.004).json()["decision"]["payout"] == 420.0
    assert pay(client, 419.999).json()["payment"]["amount"] == 420.0


def test_pay_within_limit(client):
    start(client)
    decide(client, payout=1000)
    state = pay(client, 1000).json()
    assert state["payment"]["amount"] == 1000.0
    assert state["payment"]["signed_off_by"] is None
    assert state["status"] == "decided"


def test_pay_over_limit_needs_sign_off(client):
    start(client)
    decide(client, payout=1000.01)
    response = pay(client, 1000.01)
    assert response.status_code == 409
    assert response.json() == {
        "detail": "CLM-1001 needs a handler's sign-off before payment"
    }
    assert client.get("/api/claims/CLM-1001").json()["payment"] is None


def test_pay_must_match_the_payout(client):
    start(client)
    decide(client, payout=900)
    response = pay(client, 1500)
    assert response.status_code == 409
    assert response.json() == {
        "detail": "$1,500.00 does not match the approved payout of $900.00"
    }


def test_pay_only_an_approved_claim_once(client):
    assert pay(client, 420).json() == {"detail": "CLM-1001 is not approved"}
    start(client)
    decide(client, "decline", 0)
    assert pay(client, 0).json() == {"detail": "CLM-1001 is not approved"}
    start(client, claim_id="CLM-1002")
    decide(client, payout=420, claim_id="CLM-1002")
    pay(client, 420, claim_id="CLM-1002")
    response = pay(client, 420, claim_id="CLM-1002")
    assert response.status_code == 409
    assert response.json() == {"detail": "CLM-1002 is already paid"}


def test_sign_off_pays_the_claim(client):
    start(client)
    decide(client, payout=1100)
    state = sign_off(client).json()
    assert state["status"] == "decided"
    assert state["payment"]["amount"] == 1100.0
    assert state["payment"]["signed_off_by"] == "Dana Whitfield"
    assert pay(client, 1100).json() == {"detail": "CLM-1001 is already paid"}


def test_sign_off_needs_a_claim_waiting(client):
    start(client)
    decide(client, payout=420)
    response = sign_off(client)
    assert response.status_code == 409
    assert response.json() == {"detail": "CLM-1001 is not waiting for sign-off"}


def test_sign_off_needs_a_handler_who_can(client):
    start(client)
    decide(client, payout=1100)
    response = sign_off(client, handler_id="HND-99")
    assert response.status_code == 404
    assert response.json() == {"detail": "Handler HND-99 not found"}
    with db.connect() as conn:
        handler = {
            "handler_id": "HND-04",
            "name": "Sam Lee",
            "can_approve_over_limit": False,
        }
        conn.execute(
            "INSERT INTO handlers VALUES ('HND-04', ?)", (json.dumps(handler),)
        )
    response = sign_off(client, handler_id="HND-04")
    assert response.status_code == 409
    assert response.json() == {
        "detail": "Sam Lee can't sign off payouts over the limit"
    }
