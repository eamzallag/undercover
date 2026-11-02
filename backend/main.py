"""The UnderCover backend."""

import json
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated, Any, NoReturn

from fastapi import Depends, FastAPI, HTTPException

from backend import db
from backend.models import (
    AddOn,
    Claim,
    ClaimHistory,
    ClaimState,
    ClaimSummary,
    Decision,
    DecisionRequest,
    Payment,
    PaymentRequest,
    Plan,
    Policy,
    PolicyWording,
    SignOffRequest,
    StartRequest,
    Step,
    StepRequest,
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


def state_of(conn: sqlite3.Connection, claim_id: str) -> ClaimState:
    """Return where a claim stands, without the claim as filed."""
    row = find_claim(conn, claim_id)
    return ClaimState(
        claim_id=claim_id,
        status=row["status"],
        thread_id=row["thread_id"],
        decision=decision_of(row),
        payment=payment_of(row),
    )


def approval_limit(conn: sqlite3.Connection) -> float:
    """Return the payout above which a handler must sign off."""
    row = conn.execute("SELECT data FROM company").fetchone()
    return json.loads(row["data"])["payout_approval_limit"]


def now() -> str:
    """Return the time now, in UTC."""
    return datetime.now(UTC).isoformat()


def money(amount: float) -> str:
    """Format an amount in US dollars, such as $1,250.00."""
    return f"${amount:,.2f}"


def refuse(message: str) -> NoReturn:
    """Refuse a request that the claim's state doesn't allow."""
    raise HTTPException(409, message)


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


@app.post("/api/claims/{claim_id}/start", operation_id="start_claim")
def start_claim(claim_id: str, request: StartRequest, conn: Db) -> ClaimState:
    """Mark a claim in progress for a run and clear its earlier steps."""
    row = find_claim(conn, claim_id)
    if row["status"] not in {"waiting", "in_progress"}:
        refuse(f"{claim_id} already has a decision")
    conn.execute("DELETE FROM steps WHERE claim_id = ?", (claim_id,))
    conn.execute(
        "UPDATE claims SET status = 'in_progress', thread_id = ? WHERE claim_id = ?",
        (request.thread_id, claim_id),
    )
    return state_of(conn, claim_id)


@app.post("/api/claims/{claim_id}/steps", operation_id="add_step")
def add_step(claim_id: str, request: StepRequest, conn: Db) -> Step:
    """Record one step of the agent's work on a claim."""
    find_claim(conn, claim_id)
    row = conn.execute(
        "INSERT INTO steps (claim_id, kind, title, detail, created_at) "
        "VALUES (?, ?, ?, ?, ?) RETURNING *",
        (claim_id, request.kind, request.title, request.detail, now()),
    ).fetchone()
    return Step(**dict(row))


@app.get("/api/claims/{claim_id}/steps", operation_id="list_steps")
def list_steps(claim_id: str, conn: Db) -> list[Step]:
    """List the agent's steps on a claim, in order."""
    find_claim(conn, claim_id)
    rows = conn.execute(
        "SELECT * FROM steps WHERE claim_id = ? ORDER BY step_id", (claim_id,)
    )
    return [Step(**dict(row)) for row in rows]


@app.post("/api/claims/{claim_id}/decision", operation_id="record_decision")
def record_decision(claim_id: str, request: DecisionRequest, conn: Db) -> ClaimState:
    """Record the decision on a claim: approve, decline or refer."""
    row = find_claim(conn, claim_id)
    if row["status"] != "in_progress":
        refuse(f"{claim_id} is not in progress")
    over_limit = request.decision == "approve" and request.payout > approval_limit(conn)
    conn.execute(
        "UPDATE claims SET status = ?, decision = ?, payout = ?, reasons = ?, "
        "policy_section = ?, decided_at = ? WHERE claim_id = ?",
        (
            "waiting_for_sign_off" if over_limit else "decided",
            request.decision,
            request.payout,
            request.reasons,
            request.policy_section,
            now(),
            claim_id,
        ),
    )
    return state_of(conn, claim_id)


@app.post("/api/claims/{claim_id}/payment", operation_id="pay_claim")
def pay_claim(claim_id: str, request: PaymentRequest, conn: Db) -> ClaimState:
    """Pay an approved claim its payout, if the payment rules allow it."""
    row = find_claim(conn, claim_id)
    if row["decision"] != "approve":
        refuse(f"{claim_id} is not approved")
    if row["paid_at"] is not None:
        refuse(f"{claim_id} is already paid")
    if request.amount != row["payout"]:
        refuse(
            f"{money(request.amount)} does not match the approved payout "
            f"of {money(row['payout'])}"
        )
    if row["payout"] > approval_limit(conn) and row["signed_off_by"] is None:
        refuse(f"{claim_id} needs a handler's sign-off before payment")
    conn.execute(
        "UPDATE claims SET paid_amount = ?, paid_at = ? WHERE claim_id = ?",
        (request.amount, now(), claim_id),
    )
    return state_of(conn, claim_id)


@app.post("/api/claims/{claim_id}/sign-off", operation_id="sign_off_claim")
def sign_off_claim(claim_id: str, request: SignOffRequest, conn: Db) -> ClaimState:
    """Sign off a payout over the limit as a handler, which pays it."""
    row = find_claim(conn, claim_id)
    handler = fetch_data(
        conn,
        "SELECT data FROM handlers WHERE handler_id = ?",
        request.handler_id,
        f"Handler {request.handler_id} not found",
    )
    if not handler["can_approve_over_limit"]:
        refuse(f"{handler['name']} can't sign off payouts over the limit")
    if row["status"] != "waiting_for_sign_off":
        refuse(f"{claim_id} is not waiting for sign-off")
    conn.execute(
        "UPDATE claims SET status = 'decided', paid_amount = payout, paid_at = ?, "
        "signed_off_by = ? WHERE claim_id = ?",
        (now(), handler["name"], claim_id),
    )
    return state_of(conn, claim_id)
