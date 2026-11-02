from fastapi.routing import APIRoute
from langchain_core.messages import AIMessage

from agent import main
from agent.tests.conftest import StubModel, calls
from backend.main import app


def decision(claim_id, payout, verdict="approve"):
    return (
        "record_decision",
        {
            "claim_id": claim_id,
            "decision": verdict,
            "payout": payout,
            "reasons": "The claim is covered.",
            "policy_section": "Section 3, Trip Delay",
        },
    )


def titles(client, claim_id):
    steps = client.get(f"/api/claims/{claim_id}/steps").json()
    return [step["title"] for step in steps]


def test_tools_are_api_operations():
    operations = {r.operation_id for r in app.routes if isinstance(r, APIRoute)}
    names = {t.name for t in main.TOOLS}
    assert names == {
        "get_claim",
        "get_policy",
        "get_claim_history",
        "get_policy_wording",
        "record_decision",
        "pay_claim",
    }
    assert names <= operations


def test_instructions(client):
    text = client.get("/api/instructions").json()["text"]
    assert text.startswith("You are the UnderCover Agent.")
    for tool in main.TOOLS:
        assert tool.name in text


def test_run_decides_and_pays(client):
    llm = calls(
        ("get_claim", {"claim_id": "CLM-1001"}),
        ("get_policy", {"policy_id": "POL-2001"}),
        ("get_claim_history", {"customer_id": "CUS-3001"}),
        ("get_policy_wording", {}),
        decision("CLM-1001", 420),
        ("pay_claim", {"claim_id": "CLM-1001", "amount": 420}),
        reply="Approved, paying $420.00.",
    )
    assert main.run("CLM-1001", "thread-1", llm) == "Approved, paying $420.00."

    claim = client.get("/api/claims/CLM-1001").json()
    assert claim["status"] == "decided"
    assert claim["thread_id"] == "thread-1"
    assert claim["decision"]["payout"] == 420.0
    assert claim["payment"]["amount"] == 420.0
    assert titles(client, "CLM-1001") == [
        "Reading the claim",
        "Reading the policy",
        "Reading the claim history",
        "Reading the policy wording",
        "Recording the decision",
        "Paying the claim",
        "The agent's reply",
    ]
    steps = client.get("/api/claims/CLM-1001/steps").json()
    assert "Maya Patel" in steps[0]["detail"]


def test_payment_over_limit_is_blocked(client):
    llm = calls(
        ("get_claim", {"claim_id": "CLM-1002"}),
        decision("CLM-1002", 1100),
        ("pay_claim", {"claim_id": "CLM-1002", "amount": 1100}),
    )
    main.run("CLM-1002", "thread-1", llm)

    claim = client.get("/api/claims/CLM-1002").json()
    assert claim["status"] == "waiting_for_sign_off"
    assert claim["payment"] is None
    payment_step = client.get("/api/claims/CLM-1002/steps").json()[2]
    assert payment_step["title"] == "Paying the claim"
    assert "needs a handler's sign-off" in payment_step["detail"]


def test_payment_must_match_the_payout(client):
    llm = calls(
        decision("CLM-1001", 900),
        ("pay_claim", {"claim_id": "CLM-1001", "amount": 1500}),
    )
    main.run("CLM-1001", "thread-1", llm)
    assert client.get("/api/claims/CLM-1001").json()["payment"] is None


def test_notes_become_steps(client):
    note = AIMessage(
        content="First, the claim.",
        tool_calls=[{"name": "get_claim", "args": {"claim_id": "CLM-1001"}, "id": "1"}],
    )
    llm = StubModel(messages=iter([note, AIMessage(content="Referred.")]))
    main.run("CLM-1001", "thread-1", llm)
    assert titles(client, "CLM-1001") == [
        "The agent's note",
        "Reading the claim",
        "The agent's reply",
    ]


def test_model_name(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("MODEL_NAME", raising=False)
    assert main.model().model_name == "openai/gpt-6-luna"
    monkeypatch.setenv("MODEL_NAME", "openrouter/free")
    assert main.model().model_name == "openrouter/free"
