"""Work the claims queue: `uv run -m agent`, or `uv run -m agent CLM-1001`."""

import sys
from collections import Counter
from typing import Any
from uuid import uuid4

from agent import main as agent


def waiting_claims() -> list[str]:
    """Return the ids of the claims that are waiting or in progress."""
    with agent.backend() as client:
        claims = client.get("/api/claims").raise_for_status().json()
    return [c["claim_id"] for c in claims if c["status"] in {"waiting", "in_progress"}]


def outcome(claim: dict[str, Any]) -> str:
    """Describe where a claim ended up, in one line."""
    decision = claim["decision"]
    if decision is None:
        return f"{claim['claim_id']} has no decision"
    line = f"{claim['claim_id']} {decision['decision']} ${decision['payout']:,.2f}"
    if claim["status"] == "waiting_for_sign_off":
        line += ", waiting for sign-off"
    return line


def work(claim_id: str) -> dict[str, Any]:
    """Run the agent on one claim, print the outcome and return the claim."""
    agent.run(claim_id, f"{claim_id}-{uuid4().hex[:8]}")
    with agent.backend() as client:
        claim = client.get(f"/api/claims/{claim_id}").raise_for_status().json()
    print(outcome(claim), flush=True)
    return claim


def summary(claims: list[dict[str, Any]]) -> str:
    """Count the decisions on the claims worked."""
    decisions = Counter(c["decision"]["decision"] for c in claims if c["decision"])
    waiting = sum(c["status"] == "waiting_for_sign_off" for c in claims)
    return (
        f"{len(claims)} claims: {decisions['approve']} approved, "
        f"{decisions['decline']} declined, {decisions['refer']} referred. "
        f"{waiting} wait for sign-off."
    )


def main(claim_ids: list[str]) -> None:
    """Work the claims named, or every waiting claim if none are named."""
    claims = [work(claim_id) for claim_id in claim_ids or waiting_claims()]
    if not claim_ids:
        print(summary(claims))


if __name__ == "__main__":
    main(sys.argv[1:])
