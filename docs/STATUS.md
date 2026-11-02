# Status

The pilot is being built from `docs/PLAN.md`. Phases 1 to 4 of 6 are done.

## Built

- `backend/`: FastAPI on SQLite (`backend/undercover.db`, or the path in `UNDERCOVER_DB`), seeded from `data/`.
  - Reading: `health`, `list_claims`, `get_claim`, `get_policy`, `get_claim_history` and `get_policy_wording`
  - The workflow: `start_claim`, `add_step`, `list_steps`, `record_decision`, `pay_claim` and `sign_off_claim`
  - The $1,000 rule: `pay_claim` refuses a payout over $1,000 until a handler signs off, and any amount that differs from the approved payout. `sign_off_claim` pays the claim.
  - The agent's instructions: `backend/instructions.md`, served by `get_instructions`
- `agent/`: the UnderCover Agent, LangChain's `create_agent` on OpenRouter. `run(claim_id, thread_id)` starts the claim, streams the agent and posts each step to the backend. Its six tools are the API operations `get_claim`, `get_policy`, `get_claim_history`, `get_policy_wording`, `record_decision` and `pay_claim`.
- `dashboard/`: React and Vite in the brand's fonts and colors, with light and dark mode. The queue page has a count for each status and a table of every claim, refreshing every two seconds.
- `e2e/`: Playwright tests of the queue and the light and dark themes. They run against their own backend (port 8765) and dashboard (port 5174) on a fresh database, `e2e/undercover-e2e.db`, so they never touch the data `npm run dev` uses.

## Run it

- `npm run dev` starts the backend on port 8000 and the dashboard on port 5173. The backend seeds itself the first time.
- `npm run seed` (or `uv run -m backend.seed`) resets every claim to waiting. It works while the backend runs.
- `uv run -m agent` (or `npm run agent`) works every waiting claim, one at a time. `uv run -m agent CLM-1001` works one claim. It uses `openai/gpt-6-luna`, or the model in `MODEL_NAME`.
- http://localhost:8000/docs lets you try each API operation.
- `npm run check` runs every check.
