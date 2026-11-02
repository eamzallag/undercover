"""The UnderCover database, a SQLite file seeded from data/."""

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

DEFAULT_PATH = Path(__file__).parent / "undercover.db"

TABLES = [
    "company",
    "plans",
    "add_ons",
    "policies",
    "customers",
    "handlers",
    "documents",
    "claims",
    "steps",
]

SCHEMA = """
CREATE TABLE company (data TEXT NOT NULL);
CREATE TABLE plans (plan TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE add_ons (add_on TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE policies (policy_id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE customers (customer_id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE handlers (handler_id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE documents (
    name TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    text TEXT NOT NULL
);
CREATE TABLE claims (
    claim_id TEXT PRIMARY KEY,
    policy_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    filed TEXT NOT NULL,
    status TEXT NOT NULL,
    thread_id TEXT,
    decision TEXT,
    payout REAL,
    reasons TEXT,
    policy_section TEXT,
    decided_at TEXT,
    paid_amount REAL,
    paid_at TEXT,
    signed_off_by TEXT
);
CREATE TABLE steps (
    step_id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    detail TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def db_path() -> Path:
    """Return the database file: UNDERCOVER_DB if set, else backend/undercover.db."""
    return Path(os.environ.get("UNDERCOVER_DB", DEFAULT_PATH))


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Open the database, commit on success, roll back on error, then close."""
    conn = sqlite3.connect(db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def get_db() -> Iterator[sqlite3.Connection]:
    """Give a request its own connection."""
    with connect() as conn:
        yield conn


def is_seeded() -> bool:
    """Return whether the database has its tables."""
    with connect() as conn:
        found = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'claims'"
        ).fetchone()
    return found is not None


def reset(conn: sqlite3.Connection) -> None:
    """Drop every table and create them again, empty."""
    drops = "".join(f"DROP TABLE IF EXISTS {table};\n" for table in TABLES)
    conn.executescript(drops + SCHEMA)
