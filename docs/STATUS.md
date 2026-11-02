# Status

The claims pilot from `docs/SPEC.md` is built, following `docs/PLAN.md` (all six phases done).

## Built

- `backend/`: FastAPI on SQLite (`backend/undercover.db`, or the path in `UNDERCOVER_DB`), seeded from `data/`. It never reads `data/evals/` or `data/security/`.
  - Reading: `health`, `list_claims`, `get_claim`, `get_policy`, `get_claim_history` and `get_policy_wording`
  - The workflow: `start_claim`, `add_step`, `list_steps`, `record_decision`, `pay_claim` and `sign_off_claim`
  - The $1,000 rule: `pay_claim` refuses a payout over $1,000 until a handler signs off, and any amount that differs from the approved payout. `sign_off_claim` records the handler and pays the claim.
  - The agent's instructions: `backend/instructions.md`, served by `get_instructions`
- `agent/`: the UnderCover Agent, LangChain's `create_agent` on OpenRouter. `run(claim_id, thread_id)` starts the claim, streams the agent and posts each step to the backend. Its six tools are the API operations `get_claim`, `get_policy`, `get_claim_history`, `get_policy_wording`, `record_decision` and `pay_claim`.
- `dashboard/`: React and Vite in the brand's fonts and colors, with light and dark mode. Three pages, each refreshing every two seconds where it matters:
  - the queue (`/`): a count for each status and a table of every claim
  - a claim (`/claims/CLM-1001`): the claim in full, its policy and claim history, the decision and payment, and the agent's steps as they happen
  - the agent's instructions (`/instructions`), read only
- `e2e/`: Playwright tests of the queue, a claim, the agent's work on a claim, the instructions and the light and dark themes. They run against their own backend (port 8765) and dashboard (port 5174) on a fresh database, `e2e/undercover-e2e.db`, so they never touch the data `npm run dev` uses.

## Run it

- `npm run dev` starts the backend on port 8000 and the dashboard at http://localhost:5173. The backend seeds itself the first time.
- `uv run -m agent` (or `npm run agent`) works every waiting claim, one at a time, and prints a summary. `uv run -m agent CLM-1001` works one claim. It uses `openai/gpt-6-luna`, or the model in `MODEL_NAME`.
- `npm run seed` (or `uv run -m backend.seed`) resets every claim to waiting. It works while the backend runs.
- A handler signs off a payout over $1,000 with `sign_off_claim`, for example at http://localhost:8000/docs with `{"handler_id": "HND-01"}`.
- `npm run check` runs every check.

## The first run on the queue

On November 2, 2026, with GPT-6 Luna, the agent decided all 25 claims for about $0.02: 16 approved, 6 declined and 3 referred. Three approvals were over $1,000 (CLM-1003, CLM-1008 and CLM-1011) and waited for sign-off. On the first pass the agent replied on CLM-1012 without recording its decision, which left the claim in progress. The instructions now say a decision counts only once it is recorded, and running `uv run -m agent` again finished the claim. These decisions haven't yet been scored against the handlers' own.

## Not built yet

- A Sign off button on the dashboard: handlers sign off through the API for now.
- Scoring the agent's decisions against the handlers' in `data/evals/`.
- The claims manual, sign-in, real payments and messages to customers, which the spec leaves out of the pilot.
