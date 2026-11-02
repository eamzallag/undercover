import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from backend import db
from backend.main import app
from backend.seed import DATA, seed


def test_seed_message(client):
    assert seed() == (
        "Seeded 25 claims, 50 policies, 49 customers, 3 plans and 3 handlers."
    )


def test_seeds_exactly_the_queue(client):
    queue = json.loads((DATA / "claims.json").read_text(encoding="utf-8"))
    with db.connect() as conn:
        seeded = [row[0] for row in conn.execute("SELECT claim_id FROM claims")]
    assert sorted(seeded) == sorted(claim["claim_id"] for claim in queue)


def test_reseed_resets_claims(client):
    with db.connect() as conn:
        conn.execute("UPDATE claims SET status = 'decided'")
    seed()
    assert {c["status"] for c in client.get("/api/claims").json()} == {"waiting"}


def test_seeds_on_start_up_when_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("UNDERCOVER_DB", str(tmp_path / "fresh.db"))
    assert not db.is_seeded()
    with TestClient(app) as client:
        assert len(client.get("/api/claims").json()) == 25
    assert db.is_seeded()


def decide_everything_then_fail():
    with db.connect() as conn:
        conn.execute("UPDATE claims SET status = 'decided'")
        conn.execute("SELECT * FROM no_such_table")


def test_connection_rolls_back_on_error(client):
    with pytest.raises(sqlite3.OperationalError):
        decide_everything_then_fail()
    assert {c["status"] for c in client.get("/api/claims").json()} == {"waiting"}
