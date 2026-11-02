# Status

The pilot is being built from `docs/PLAN.md`. Phase 1 of 6 is done.

## Built

- `backend/`: FastAPI on SQLite (`backend/undercover.db`, or the path in `UNDERCOVER_DB`), seeded from `data/`. The read operations: `health`, `list_claims`, `get_claim`, `get_policy`, `get_claim_history` and `get_policy_wording`.
- `agent/`: still the skeleton, `run(claim_id, thread_id)` with one tool that calls the health route
- `dashboard/`: still the skeleton, one page that shows whether the backend is up
- `e2e/`: one test of that page

## Run it

- `npm run dev` starts the backend on port 8000 and the dashboard on port 5173. The backend seeds itself the first time.
- `npm run seed` (or `uv run -m backend.seed`) resets every claim to waiting. It works while the backend runs.
- http://localhost:8000/docs lets you try each API operation.
- `npm run check` runs every check.
