"""The UnderCover Agent, which decides claims through the backend's API."""

import os
from collections.abc import Iterable
from typing import Any, Literal

import httpx
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

load_dotenv(override=True)

BACKEND_URL = "http://127.0.0.1:8000"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-6-luna"

STEP_TITLES = {
    "get_claim": "Reading the claim",
    "get_policy": "Reading the policy",
    "get_claim_history": "Reading the claim history",
    "get_policy_wording": "Reading the policy wording",
    "record_decision": "Recording the decision",
    "pay_claim": "Paying the claim",
}


def backend() -> httpx.Client:
    """Return a client for the UnderCover backend."""
    return httpx.Client(base_url=BACKEND_URL, timeout=30)


def call(method: str, path: str, body: dict[str, Any] | None = None) -> str:
    """Call the backend and return its reply as text, including any refusal."""
    with backend() as client:
        return client.request(method, path, json=body).text


@tool
def get_claim(claim_id: str) -> str:
    """Get a claim in full: the story, the items claimed and the documents."""
    return call("GET", f"/api/claims/{claim_id}")


@tool
def get_policy(policy_id: str) -> str:
    """Get a policy, with its plan's limits and the add-ons the customer bought."""
    return call("GET", f"/api/policies/{policy_id}")


@tool
def get_claim_history(customer_id: str) -> str:
    """Get a customer's earlier claims."""
    return call("GET", f"/api/customers/{customer_id}/history")


@tool
def get_policy_wording() -> str:
    """Get the policy wording, the contract with the customer."""
    return call("GET", "/api/policy-wording")


@tool
def record_decision(
    claim_id: str,
    decision: Literal["approve", "decline", "refer"],
    payout: float,
    reasons: str,
    policy_section: str,
) -> str:
    """Record the decision on a claim.

    The payout is in US dollars, and $0 for a decline or a referral. The reasons
    are two or three plain sentences. The policy section is the section of the
    wording the decision relies on, such as "Section 3, Trip Delay".
    """
    return call(
        "POST",
        f"/api/claims/{claim_id}/decision",
        {
            "decision": decision,
            "payout": payout,
            "reasons": reasons,
            "policy_section": policy_section,
        },
    )


@tool
def pay_claim(claim_id: str, amount: float) -> str:
    """Pay an approved claim its payout, in US dollars."""
    return call("POST", f"/api/claims/{claim_id}/payment", {"amount": amount})


TOOLS = [
    get_claim,
    get_policy,
    get_claim_history,
    get_policy_wording,
    record_decision,
    pay_claim,
]


def model() -> ChatOpenAI:
    """Return the model named in MODEL_NAME, or GPT-6 Luna by default."""
    name = os.getenv("MODEL_NAME")
    return ChatOpenAI(
        model=name or DEFAULT_MODEL,
        base_url=OPENROUTER_BASE_URL,
        api_key=SecretStr(os.environ["OPENROUTER_API_KEY"]),
        reasoning_effort=None if name else "low",
    )


def step_of(message: BaseMessage) -> dict[str, str] | None:
    """Describe a message as a step on the claim, or None if it says nothing."""
    if isinstance(message, ToolMessage):
        name = message.name or "tool"
        return {
            "kind": "tool",
            "title": STEP_TITLES.get(name, name),
            "detail": message.text,
        }
    if isinstance(message, AIMessage) and message.text:
        title = "The agent's note" if message.tool_calls else "The agent's reply"
        return {"kind": "message", "title": title, "detail": message.text}
    return None


def record_steps(claim_id: str, messages: Iterable[BaseMessage]) -> None:
    """Post each message that says something to the backend as a step."""
    for message in messages:
        step = step_of(message)
        if step:
            with backend() as client:
                client.post(f"/api/claims/{claim_id}/steps", json=step)


def run(claim_id: str, thread_id: str, llm: BaseChatModel | None = None) -> str:
    """Run the agent on one claim, recording its steps, and return its final reply."""
    with backend() as client:
        instructions = client.get("/api/instructions").raise_for_status().json()
        client.post(
            f"/api/claims/{claim_id}/start", json={"thread_id": thread_id}
        ).raise_for_status()

    agent = create_agent(
        llm or model(), tools=TOOLS, system_prompt=instructions["text"]
    )
    reply = ""
    for update in agent.stream(
        {"messages": [{"role": "user", "content": f"Decide claim {claim_id}."}]},
        config={"configurable": {"thread_id": thread_id}},
        stream_mode="updates",
    ):
        for node in update.values():
            messages = node["messages"]
            record_steps(claim_id, messages)
            reply = next((m.text for m in messages if isinstance(m, AIMessage)), reply)
    return reply
