"""Load UnderCover's records from data/ into the database, with every claim waiting."""

import json
from pathlib import Path
from typing import Any

from backend import db

DATA = Path(__file__).parent.parent / "data"


def load(name: str) -> Any:
    """Read one JSON file from data/."""
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def seed() -> str:
    """Replace the database's contents with the records in data/."""
    company = load("company.json")
    plans = load("plans.json")
    policies = load("policies.json")
    customers = load("customers.json")
    handlers = load("handlers.json")
    claims = load("claims.json")
    wording = (DATA / "policy_wording.md").read_text(encoding="utf-8")

    with db.connect() as conn:
        db.reset(conn)
        conn.execute("INSERT INTO company VALUES (?)", (json.dumps(company),))
        conn.executemany(
            "INSERT INTO plans VALUES (?, ?)",
            [(plan["plan"], json.dumps(plan)) for plan in plans["plans"]],
        )
        conn.executemany(
            "INSERT INTO add_ons VALUES (?, ?)",
            [(add_on["add_on"], json.dumps(add_on)) for add_on in plans["add_ons"]],
        )
        conn.executemany(
            "INSERT INTO policies VALUES (?, ?)",
            [(policy["policy_id"], json.dumps(policy)) for policy in policies],
        )
        conn.executemany(
            "INSERT INTO customers VALUES (?, ?)",
            [(customer["customer_id"], json.dumps(customer)) for customer in customers],
        )
        conn.executemany(
            "INSERT INTO handlers VALUES (?, ?)",
            [(handler["handler_id"], json.dumps(handler)) for handler in handlers],
        )
        conn.execute(
            "INSERT INTO documents VALUES ('policy_wording', ?, ?)",
            (company["policy_wording_version"], wording),
        )
        conn.executemany(
            "INSERT INTO claims (claim_id, policy_id, customer_id, filed, status) "
            "VALUES (?, ?, ?, ?, 'waiting')",
            [
                (
                    claim["claim_id"],
                    claim["policy_id"],
                    claim["customer_id"],
                    json.dumps({k: v for k, v in claim.items() if k != "status"}),
                )
                for claim in claims
            ],
        )

    return (
        f"Seeded {len(claims)} claims, {len(policies)} policies, "
        f"{len(customers)} customers, {len(plans['plans'])} plans "
        f"and {len(handlers)} handlers."
    )


if __name__ == "__main__":
    print(seed())
