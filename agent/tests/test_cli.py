from agent import __main__ as cli
from agent import main


def refer_everything(client, worked):
    """A stand-in for the agent that refers each claim it's given."""

    def run(claim_id, thread_id):
        worked.append((claim_id, thread_id))
        client.post(f"/api/claims/{claim_id}/start", json={"thread_id": thread_id})
        client.post(
            f"/api/claims/{claim_id}/decision",
            json={
                "decision": "refer",
                "payout": 0,
                "reasons": "It needs a handler.",
                "policy_section": "Section 11, How to claim",
            },
        )

    return run


def test_works_only_waiting_claims(client, monkeypatch, capsys):
    worked = []
    client.post("/api/claims/CLM-1001/start", json={"thread_id": "earlier"})
    client.post(
        "/api/claims/CLM-1001/decision",
        json={
            "decision": "approve",
            "payout": 1100,
            "reasons": "Covered.",
            "policy_section": "Section 5",
        },
    )
    client.post("/api/claims/CLM-1002/start", json={"thread_id": "stopped"})
    monkeypatch.setattr(main, "run", refer_everything(client, worked))

    cli.main([])

    claim_ids = [claim_id for claim_id, _ in worked]
    assert "CLM-1001" not in claim_ids
    assert "CLM-1002" in claim_ids
    assert len(claim_ids) == 24
    assert all(thread.startswith(claim_id) for claim_id, thread in worked)
    output = capsys.readouterr().out.splitlines()
    assert output[0] == "CLM-1002 refer $0.00"
    assert (
        output[-1]
        == "24 claims: 0 approved, 0 declined, 24 referred. 0 wait for sign-off."
    )


def test_works_one_claim(client, monkeypatch, capsys):
    worked = []
    monkeypatch.setattr(main, "run", refer_everything(client, worked))
    cli.main(["CLM-1003"])
    assert [claim_id for claim_id, _ in worked] == ["CLM-1003"]
    assert capsys.readouterr().out == "CLM-1003 refer $0.00\n"


def test_outcome_lines():
    claim = {"claim_id": "CLM-1002", "status": "in_progress", "decision": None}
    assert cli.outcome(claim) == "CLM-1002 has no decision"
    claim = {
        "claim_id": "CLM-1002",
        "status": "waiting_for_sign_off",
        "decision": {"decision": "approve", "payout": 1100.0},
    }
    assert cli.outcome(claim) == "CLM-1002 approve $1,100.00, waiting for sign-off"
    assert cli.summary([claim]) == (
        "1 claims: 1 approved, 0 declined, 0 referred. 1 wait for sign-off."
    )
