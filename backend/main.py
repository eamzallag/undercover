"""The UnderCover backend."""

import json
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException

from backend import db
from backend.models import (
    AddOn,
    Claim,
    ClaimHistory,
    ClaimSummary,
    Decision,
    Payment,
    Plan,
    Policy,
    PolicyWording,
)
from backend.seed import seed


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Seed the database on start-up if it has never been seeded."""
    if not db.is_seeded():
        seed()
    yield


app = FastAPI(title="UnderCover", lifespan=lifespan)

Db = Annotated[sqlite3.Connection, Depends(db.get_db)]

CLAIMS = (
    "SELECT claims.*, json_extract(customers.data, '$.name') AS customer_name "
    "FROM claims JOIN customers USING (customer_id) "
)


def fetch_data(
    conn: sqlite3.Connection, query: str, key: str, missing: str
) -> dict[str, Any]:
    """Return the JSON record a query finds by its key, or a 404."""
    row = conn.execute(query, (key,)).fetchone()
    if row is None:
        raise HTTPException(404, missing)
    return json.loads(row["data"])


def find_claim(conn: sqlite3.Connection, claim_id: str) -> sqlite3.Row:
    """Return a claim's row, or a 404."""
    row = conn.execute(CLAIMS + "WHERE claim_id = ?", (claim_id,)).fetchone()
    if row is None:
        raise HTTPException(404, f"Claim {claim_id} not found")
    return row


def decision_of(row: sqlite3.Row) -> Decision | None:
    """Return the decision recorded on a claim, if any."""
    if row["decision"] is None:
        return None
    return Decision(
        decision=row["decision"],
        payout=row["payout"],
        reasons=row["reasons"],
        policy_section=row["policy_section"],
        decided_at=row["decided_at"],
    )


def payment_of(row: sqlite3.Row) -> Payment | None:
    """Return the payment made on a claim, if any."""
    if row["paid_at"] is None:
        return None
    return Payment(
        amount=row["paid_amount"],
        paid_at=row["paid_at"],
        signed_off_by=row["signed_off_by"],
    )


def claim_of(row: sqlite3.Row) -> Claim:
    """Build a claim in full from its row."""
    return Claim(
        **json.loads(row["filed"]),
        customer_name=row["customer_name"],
        status=row["status"],
        thread_id=row["thread_id"],
        decision=decision_of(row),
        payment=payment_of(row),
    )


@app.get("/api/health", operation_id="health")
def health() -> dict[str, str]:
    """Check that the backend is running."""
    return {"status": "ok"}


@app.get("/api/claims", operation_id="list_claims")
def list_claims(conn: Db) -> list[ClaimSummary]:
    """List every claim in the queue with where it stands."""
    rows = conn.execute(CLAIMS + "ORDER BY claim_id").fetchall()
    return [
        ClaimSummary(
            **json.loads(row["filed"]),
            customer_name=row["customer_name"],
            status=row["status"],
            decision=row["decision"],
            payout=row["payout"],
        )
        for row in rows
    ]


@app.get("/api/claims/{claim_id}", operation_id="get_claim")
def get_claim(claim_id: str, conn: Db) -> Claim:
    """Get a claim in full, with its decision and payment."""
    return claim_of(find_claim(conn, claim_id))


@app.get("/api/policies/{policy_id}", operation_id="get_policy")
def get_policy(policy_id: str, conn: Db) -> Policy:
    """Get a policy, with its plan's limits and its add-ons."""
    policy = fetch_data(
        conn,
        "SELECT data FROM policies WHERE policy_id = ?",
        policy_id,
        f"Policy {policy_id} not found",
    )
    plan = fetch_data(
        conn,
        "SELECT data FROM plans WHERE plan = ?",
        policy["plan"],
        f"Plan {policy['plan']} not found",
    )
    add_ons = {
        row["add_on"]: AddOn(**json.loads(row["data"]))
        for row in conn.execute("SELECT add_on, data FROM add_ons")
    }
    return Policy(
        **policy,
        plan_details=Plan(**plan),
        add_on_details=[add_ons[name] for name in policy["add_ons"]],
    )


@app.get("/api/customers/{customer_id}/history", operation_id="get_claim_history")
def get_claim_history(customer_id: str, conn: Db) -> ClaimHistory:
    """Get a customer's name and earlier claims, without their contact details."""
    customer = fetch_data(
        conn,
        "SELECT data FROM customers WHERE customer_id = ?",
        customer_id,
        f"Customer {customer_id} not found",
    )
    return ClaimHistory(**customer)


@app.get("/api/policy-wording", operation_id="get_policy_wording")
def get_policy_wording(conn: Db) -> PolicyWording:
    """Get the policy wording and its version."""
    row = conn.execute(
        "SELECT version, text FROM documents WHERE name = 'policy_wording'"
    ).fetchone()
    return PolicyWording(version=row["version"], text=row["text"])
