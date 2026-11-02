# Status

The pilot is being built from `docs/PLAN.md`. Phases 1 and 2 of 6 are done.

## Built

- `backend/`: FastAPI on SQLite (`backend/undercover.db`, or the path in `UNDERCOVER_DB`), seeded from `data/`.
  - Reading: `health`, `list_claims`, `get_claim`, `get_policy`, `get_claim_history` and `get_policy_wording`
  - The workflow: `start_claim`, `add_step`, `list_steps`, `record_decision`, `pay_claim` and `sign_off_claim`
  - The $1,000 rule: `pay_claim` refuses a payout over $1,000 until a handler signs off, and any amount that differs from the approved payout. `sign_off_claim` pays the claim.
- `agent/`: still the skeleton, `run(claim_id, thread_id)` with one tool that calls the health route
- `dashboard/`: still the skeleton, one page that shows whether the backend is up
- `e2e/`: one test of that page

## Run it

- `npm run dev` starts the backend on port 8000 and the dashboard on port 5173. The backend seeds itself the first time.
- `npm run seed` (or `uv run -m backend.seed`) resets every claim to waiting. It works while the backend runs.
- http://localhost:8000/docs lets you try each API operation.
- `npm run check` runs every check.
