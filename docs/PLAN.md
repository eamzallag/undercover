# Plan: the claims pilot

This plan builds the pilot in `docs/SPEC.md`:

- a backend that holds UnderCover's claims
- the UnderCover Agent, which decides them
- a dashboard where the claims team watches the queue, each claim, the agent's steps and its instructions

It follows `docs/TECH_STACK.md`, `docs/CODE_STANDARDS.md`, `docs/PROCESS.md` and `docs/BRAND.md`.

There are six phases, and each builds on the one before:

1. **The backend's records:** the data in SQLite and the operations that read it
2. **The claim workflow:** the operations that change a claim, and the $1,000 rule
3. **The UnderCover Agent:** its instructions, its tools and the command that works the queue
4. **The dashboard and the queue:** the brand, the layout and the queue page
5. **The claim page:** each claim in full, the agent's steps as it works, and the instructions
6. **The whole queue:** the agent on all 25 claims with a real model, checked end to end

Each phase ends with its tests, every check passing, `docs/STATUS.md` updated and a commit.

## How it fits together

```
dashboard (React, :5173) ──polls every 2s──> backend (FastAPI, :8000) <──> SQLite (backend/undercover.db)
                                                   ^                              ^
agent (uv run -m agent) ──tools = API operations───┘                              └── seeded from data/
        │
        └──> OpenRouter (openai/gpt-6-luna, or MODEL_NAME)
```

A claim moves through four statuses:

```
waiting ──start──> in progress ──decision──> decided
                        │
                        └──approve over $1,000──> waiting for sign-off ──a handler signs off──> decided
```

## Key choices, and why

- **SQLite through Python's built-in `sqlite3`, with no ORM.** The pilot has a handful of tables, and SQLAlchemy isn't installed. A claim as filed (the story, items and documents) never changes, so it's stored as JSON. What does change (the status, the decision and the payment) gets its own columns. Policies, customers, plans and handlers are stored as JSON by their ids. The seed loads named files from `data/` and never reads `data/evals/` or `data/security/`.
- **The backend is the only way in.** The agent reaches claims, records and its instructions only through the API. Each agent tool is one API operation with the same name, so the agent can do exactly what the API allows and nothing more.
- **The $1,000 rule is enforced by the backend, not the prompt.** The instructions tell the agent not to pay over $1,000, but `pay_claim` is what stops it. It refuses a payout over the limit until a handler signs off. It also refuses any amount that differs from the approved payout, so the agent can't approve $900 and then pay $1,500. A handler's sign-off releases the payment. The limit comes from `data/company.json`.
- **A referral counts as decided.** The agent's work on the claim is done, so the queue shows "Decided" with the decision "Refer".
- **The agent's runner records its steps, not the model.** `run()` streams the agent and posts each tool result and each message to the backend as a step, so the record is complete whatever the model does. The dashboard polls every two seconds. That's live enough for one agent on one claim, and much simpler than websockets.
- **The agent sees only what it needs.** The claim history operation returns the customer's name and earlier claims. It leaves out their address, phone, email and date of birth, which `data/README.md` marks as personal data.
- **The instructions live with the backend** in `backend/instructions.md` and are served read only by `get_instructions`. The agent fetches them at the start of each run, and the dashboard shows the same text.
- **The policy wording comes through a tool,** so reading it shows as a step on the dashboard. It's the full `data/policy_wording.md`, about 2,000 tokens.
- **The agent runs from the command line.** `uv run -m agent` works every waiting claim one at a time, and `uv run -m agent CLM-1001` works one. The spec asks the dashboard to show the work, not to start it.
- **The end-to-end tests get their own backend and database** on ports 8001 and 5174, seeded fresh for each run. That way `npm run check` never changes your data while `npm run dev` is running.

## The API

Every operation has an `operation_id`, a one-line docstring and no optional inputs. The agent's six tools are the operations marked with \*.

| Operation | Method and path | What it does |
|---|---|---|
| `health` | GET /api/health | Already built |
| `list_claims` | GET /api/claims | The queue: each claim's id, customer, type, summary, amount claimed, status, decision and payout |
| `get_claim`\* | GET /api/claims/{claim_id} | A claim in full, with its decision and payment |
| `get_policy`\* | GET /api/policies/{policy_id} | A policy, with its plan's limits |
| `get_claim_history`\* | GET /api/customers/{customer_id}/history | The customer's name and earlier claims |
| `get_policy_wording`\* | GET /api/policy-wording | The policy wording and its version |
| `get_instructions` | GET /api/instructions | The agent's instructions |
| `start_claim` | POST /api/claims/{claim_id}/start | Mark a claim in progress for a run (by thread id) and clear its earlier steps |
| `add_step` | POST /api/claims/{claim_id}/steps | Record one step of the agent's work |
| `list_steps` | GET /api/claims/{claim_id}/steps | The agent's steps on a claim, in order |
| `record_decision`\* | POST /api/claims/{claim_id}/decision | Record approve, decline or refer, with the payout, the reasons and the policy section |
| `pay_claim`\* | POST /api/claims/{claim_id}/payment | Pay an approved claim its payout, if the rules allow |
| `sign_off_claim` | POST /api/claims/{claim_id}/sign-off | A handler signs off a payout over $1,000, which releases the payment |

The agent's runner calls `get_instructions`, `start_claim` and `add_step`; the model never does. A refused request comes back with a plain message, such as "CLM-1002 needs a handler's sign-off before payment". The agent's tools pass that message on to the model instead of stopping the run.

While `npm run dev` is running, you can try every operation in the browser at http://localhost:8000/docs.

## Not in this plan

- The claims manual, sign-in, real payments and messages to customers, as the spec says
- `data/knowledge.json` and `data/security/`, which the spec doesn't ask for
- Scoring the agent against `data/evals/` (see the questions at the end)
- Starting the agent from the dashboard, or running several agents at once

## Phase 1: The backend's records

**What it builds**

- `backend/db.py`: the SQLite connection and the schema. The database is `backend/undercover.db`, which git ignores, or the path in `UNDERCOVER_DB` if that is set. Tests and the end-to-end run set it.
- `backend/seed.py`: `uv run -m backend.seed` (or `npm run seed`) drops and reloads every table from `data/` and sets every claim to waiting. The backend seeds itself on start-up when the database is missing, so `npm run dev` works on a fresh clone.
- `backend/models.py`: Pydantic models for the responses
- The read operations: `list_claims`, `get_claim`, `get_policy`, `get_claim_history` and `get_policy_wording`
- Tests, with a fixture that gives each test a fresh, seeded database in a temporary folder

**Why first:** everything else reads these records, and each step of the work needs a database it can reset.

**Success criteria**

- [x] `uv run -m backend.seed` prints `Seeded 25 claims, 50 policies, 49 customers, 3 plans and 3 handlers.`
- [x] `GET /api/claims` returns 25 claims, CLM-1001 to CLM-1025, all with `"status": "waiting"`. CLM-1001's customer is Maya Patel.
- [x] `GET /api/claims/CLM-1001` returns the story, 3 items totaling $420.00 and 4 documents, with `decision` and `payment` both null.
- [x] `GET /api/claims/CLM-9999` returns 404 with `{"detail": "Claim CLM-9999 not found"}`. An unknown policy or customer gets the same kind of 404.
- [x] `GET /api/policies/POL-2001` returns the Premium plan with its limits (a Trip Delay maximum of $800 and a deductible of $50), no add-ons, and the trip to Rome.
- [x] `GET /api/customers/CUS-3001/history` returns Maya Patel and her one earlier claim, CLM-0412. It has no email, phone, address or date of birth.
- [x] `GET /api/policy-wording` returns version `2026.1` and the wording's text.
- [x] A test reads the app's routes and OpenAPI schema. It fails if any operation has no `operation_id`, has no docstring or one longer than a line, or has an optional input.
- [x] A test checks that the seeded claims are exactly the 25 in `data/claims.json`, and `git grep -n evals -- backend agent dashboard` finds nothing.
- [x] `uv run -m backend.seed` resets the data while the backend is running, without a restart.
- [x] `npm run check:python` passes with coverage of at least 80%.

## Phase 2: The claim workflow and the $1,000 rule

**What it builds**

`start_claim`, `add_step`, `list_steps`, `record_decision`, `pay_claim` and `sign_off_claim`, with these rules:

- `start_claim` works on a claim that's waiting or in progress, so a run that stopped part way can start again. It clears the claim's steps and records the thread id. On any other claim it's refused.
- `add_step` takes a kind (`tool` or `message`), a title and a detail.
- `record_decision` works only on a claim in progress:
  - Decline and refer carry a payout of $0, and approve carries a payout above $0.
  - The reasons and the policy section can't be empty.
  - An approval over the limit goes to waiting for sign-off. Every other decision goes to decided.
- `pay_claim` pays only an approved, unpaid claim, and only exactly its payout. The payout must be $1,000.00 or less, or a handler must have signed off.
- `sign_off_claim` works only on a claim waiting for sign-off, by a handler in `data/handlers.json` who can approve over the limit. It records the handler's name and the time, pays the payout and marks the claim decided.
- Amounts are rounded to the cent.

**Why now:** the rules get built and tested on their own, before any model can call them. The spec says the system must block the payment even if the agent tries to pay, so the guard has to be in the backend.

**Success criteria**

- [x] Tests cover every rule above, with each allowed and each refused case. They include the boundary: a payout of $1,000.00 pays straight away, and $1,000.01 waits for sign-off.
- [x] Against the running backend, this sequence gives these responses. The amounts only check the mechanics; they aren't a decision on CLM-1002.
  1. `POST /api/claims/CLM-1002/start` with `{"thread_id": "check-1"}` returns status `in_progress`
  2. `POST /api/claims/CLM-1002/steps` with `{"kind": "message", "title": "Check", "detail": "A test step"}`, then `GET /api/claims/CLM-1002/steps`, returns that one step
  3. `POST /api/claims/CLM-1002/decision` with `{"decision": "approve", "payout": 1100, "reasons": "A check.", "policy_section": "Section 5, Baggage and Personal Effects"}` returns status `waiting_for_sign_off`
  4. `POST /api/claims/CLM-1002/payment` with `{"amount": 1100}` returns 409, "CLM-1002 needs a handler's sign-off before payment"
  5. `POST /api/claims/CLM-1002/sign-off` with `{"handler_id": "HND-01"}` returns status `decided`, paid $1,100.00, signed off by Dana Whitfield
  6. `POST /api/claims/CLM-1002/payment` with `{"amount": 1100}` returns 409, because the claim is already paid
  7. After `uv run -m backend.seed`, CLM-1002 is waiting again, with no steps
- [x] `npm run check:python` passes.

## Phase 3: The UnderCover Agent

**What it builds**

- `backend/instructions.md` and `get_instructions`. The instructions tell the agent to:
  - read the claim, the policy, the claim history and the policy wording, in that order
  - decide from the policy wording alone:
    - approve a covered claim that has its documents
    - decline when the wording excludes the claim or its conditions aren't met
    - refer when the claim needs a person's judgment or more information, such as a missing document
  - work out the payout as section 10 of the wording sets out: the per-item limits (including Electronics Plus), minus anything a carrier has already paid, minus the deductible once per claim where it applies, and up to the benefit's maximum
  - record the decision with two or three plain sentences and the section of the wording it relies on
  - pay an approval of $1,000 or less, for exactly the payout, and leave a larger one for a handler's sign-off
- `agent/main.py`:
  - six tools, one for each operation marked \* above, each a thin call to the API
  - `run(claim_id, thread_id)`, which fetches the instructions, starts the claim, streams the agent, posts each step and returns the agent's final reply
  - a plain English title for each step, such as "Reading the policy" or "Paying the claim"
  - the backend's address changes to `127.0.0.1`, and the skeleton's `check_backend` tool goes
- `agent/__main__.py`: `uv run -m agent` (or `npm run agent`) works every claim that's waiting or in progress, one at a time, with a new thread id for each. It prints one line per claim, such as `CLM-1001 approve $420.00`, and a summary at the end. `uv run -m agent CLM-1001` works one claim.
- Tests with a stub model, run against the real backend app and a fresh database

The model doesn't change from the skeleton: `openai/gpt-6-luna` at low reasoning effort, or `MODEL_NAME` if it's set.

**Why now:** the backend's rules are in place, so the agent can be built and tested against them. Building it before the dashboard gives the dashboard real decisions and steps to show.

**Success criteria**

- [x] `GET /api/instructions` returns the instructions.
- [x] Test: a stub model reads CLM-1001, its policy, its history and the wording, approves $420.00 under Section 3 and pays $420.00. The claim ends decided and paid $420.00, with one step for each tool call and one for the final reply, in order.
- [x] Test: a stub model approves CLM-1002 for $1,100.00 and then tries to pay it. The payment is refused, the claim waits for sign-off unpaid, and the refusal shows in the steps.
- [x] Test: a stub model approves $900.00 and then tries to pay $1,500.00. The payment is refused and nothing is paid.
- [x] Test: the agent's tool names match the API's operation ids.
- [x] Test: with `run` stubbed, `uv run -m agent` works only the claims that are waiting or in progress.
- [x] With the real model, at a fraction of a cent, `uv run -m backend.seed` and then `uv run -m agent CLM-1001`:
  - prints one line with a decision and a payout
  - leaves `GET /api/claims/CLM-1001` showing the decision, two or three sentences of reasons and a policy section
  - leaves `GET /api/claims/CLM-1001/steps` showing the claim, policy, history and wording being read, the decision being recorded, and the final reply
- [x] `npm run check:python` passes.

## Phase 4: The dashboard and the queue

**What it builds**

- **The brand:** Instrument Sans, Instrument Serif (for a short tagline) and JetBrains Mono from Google Fonts. The colors are CSS variables for light and dark mode, following the system setting. Panels are rounded, with no outlines.
- **Pages:** `react-router` with three pages: the queue (`/`), a claim (`/claims/:claimId`) and the instructions (`/instructions`). A header has the UnderCover name and links to the queue and the instructions.
- **`dashboard/src/api.ts`:** types that match the API, and a small hook that fetches data and refreshes it every two seconds.
- **The queue page:**
  - a tile for each status with its count: Waiting in Marigold, In progress in Cerulean, Waiting for sign-off in Coral and Decided in Sea Green
  - a table with each claim's id, customer, type, summary, amount claimed, status, decision and payout
  - decision badges: Approve in Sea Green, Refer in Marigold, Decline in Coral
  - ids and amounts in JetBrains Mono, with money shown as $1,250.00
- **`playwright.config.ts`:** the end-to-end run gets its own backend, on port 8001 with `e2e/undercover-e2e.db` seeded fresh. It also gets its own dashboard on port 5174, whose API proxy points at port 8001 through `UNDERCOVER_API` in `vite.config.ts`.
- The queue replaces the skeleton's health page and its tests. The health route stays, because Playwright uses it to know the backend is up.

**Why now:** the backend and agent are producing real data. The queue is the team's main screen, and setting the brand and layout here means the claim page only has to add content.

**Success criteria**

- [ ] vitest: the queue renders a stubbed API's claims, with status labels, counts per status and money such as `$1,150.00`. Each claim links to its page, and a status change shows up on the next refresh.
- [ ] Playwright: the queue shows 25 claims, including CLM-1001 for Maya Patel, Trip delay, $420.00, Waiting.
- [ ] Playwright: the page background is `#F0F4F5` in light mode and `#04232E` in dark mode.
- [ ] Running `npm run e2e` while `npm run dev` is running leaves the dev database as it was.
- [ ] Playwright MCP, with `npm run dev` running: http://localhost:5173 shows the header, the four tiles and 25 rows in the brand's fonts and colors. Panels have no border on one edge and there's no line across the top of the page. Take screenshots in light and dark mode.
- [ ] Playwright MCP: with the queue open, `uv run -m agent CLM-1001` moves CLM-1001 from Waiting to In progress to Decided without a reload.
- [ ] `npm run check:ts` and `npm run e2e` pass.

## Phase 5: The claim page, the agent's steps and the instructions

**What it builds**

- **The claim page:**
  - The claim: the customer, type, dates and place, the story, the items with their total, and each document with its text.
  - The policy: the plan, add-ons, trip dates, trip cost and travelers, and the customer's earlier claims.
  - The decision: approve, decline or refer, with the payout, the reasons and the policy section.
  - The payment, which is one of:
    - paid, with the date, and the handler if one signed off
    - waiting for a handler's sign-off
    - not paid
  - The agent's steps: numbered, each with its title and time and its detail folded away. They refresh every two seconds, so new steps appear while the agent works.
  - "The agent hasn't worked this claim yet" for a waiting claim, and "Claim not found" for an unknown id.
- **The instructions page:** the text from `get_instructions` as written, marked read only, with nothing to edit.

**Why now:** these are the rest of the spec's screens, built on the layout and data hook from Phase 4.

**Success criteria**

- [ ] vitest: the claim page renders each part for a waiting claim, an in-progress claim, a claim waiting for sign-off, a paid claim and a declined claim, and shows "Claim not found" for an unknown id.
- [ ] vitest: new steps appear on the next refresh.
- [ ] vitest: the instructions page shows the text and has no input, text area or button.
- [ ] Playwright: clicking CLM-1001 in the queue opens its page, with the story, the three items totaling $420.00, the four documents and the Premium plan.
- [ ] Playwright: the test plays the agent's part on CLM-1002 through the API (start, two steps, then approve for $1,100.00). The claim's page then shows:
  - the status Waiting for sign-off
  - the reasons and the policy section
  - both steps, in order
  - "Payment of $1,100.00 waits for a handler's sign-off"

  The queue shows the same status.
- [ ] Playwright: the instructions page shows the instructions.
- [ ] Playwright MCP: with `npm run dev` running and http://localhost:5173/claims/CLM-1003 open, `uv run -m agent CLM-1003` makes the steps appear one at a time without a reload, followed by the decision. Take screenshots in light and dark mode.
- [ ] `npm run check` passes.

## Phase 6: The whole queue

**What it builds**

Nothing new, unless the run finds a problem:

1. Run the agent on the whole queue with the real model.
2. Check the results through the API and the dashboard.
3. Fix whatever is wrong.
4. Bring `docs/STATUS.md` up to date.

**Why last:** this is the pilot doing its job from start to finish, the way the claims team will use it. The other phases tested each part; this one tests them together on real claims.

**Success criteria**

- [ ] After `uv run -m backend.seed`, `uv run -m agent` works all 25 claims. It ends with a summary such as `25 claims: 14 approved, 6 declined, 5 referred. 4 wait for sign-off.` The numbers depend on the model, and the run should cost a few cents.
- [ ] `GET /api/claims` shows no claim waiting or in progress.
- [ ] Every approval over $1,000 is waiting for sign-off and unpaid, and every other approval is paid exactly its payout. Declines and referrals have a payout of $0 and no payment.
- [ ] Every decision has reasons and a policy section.
- [ ] Playwright MCP: the queue shows the final counts. An approved claim, a declined claim, a referred claim and a claim waiting for sign-off each show their decision, reasons, policy section and steps.
- [ ] Sign off one waiting claim as HND-01 at http://localhost:8000/docs. Its page then shows it paid and signed off by Dana Whitfield.
- [ ] `docs/STATUS.md` says what's built, how to run it (`npm run dev`, `npm run seed` and `uv run -m agent`) and what isn't built yet.
- [ ] `npm run check` passes, and the results are reported.

## Questions for your review

1. **Sign-off on the dashboard.** The spec's screens are for seeing, so in this plan handlers sign off through the API, which you can try at `/docs`. Should the claim page have a Sign off button too? It's small: a choice of handler and a button.
2. **Scoring against the handlers' decisions.** Phase 6 checks that the agent's decisions are well formed, not that they're right, because `docs/PROCESS.md` says not to open `data/evals/` unless asked. Would you like a script that scores the run against `data/evals/decisions.json`? The agent would still never see that file.
