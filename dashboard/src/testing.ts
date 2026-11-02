import { vi } from "vitest";
import type { Claim, ClaimHistory, ClaimSummary, Policy, Step } from "./api";

export type Routes = Record<string, unknown>;

export function stubApi(routes: Routes) {
  vi.stubGlobal(
    "fetch",
    vi.fn((path: string) =>
      Promise.resolve(
        path in routes
          ? Response.json(routes[path])
          : Response.json({ detail: "Not Found" }, { status: 404 }),
      ),
    ),
  );
}

export function summary(overrides: Partial<ClaimSummary>): ClaimSummary {
  return {
    claim_id: "CLM-1001",
    customer_name: "Maya Patel",
    claim_type: "trip_delay",
    summary: "Flight home canceled by the airline",
    submitted_on: "2026-06-24",
    amount_claimed: 420,
    status: "waiting",
    decision: null,
    payout: null,
    ...overrides,
  };
}

export function claim(overrides: Partial<Claim>): Claim {
  return {
    claim_id: "CLM-1001",
    policy_id: "POL-2001",
    customer_id: "CUS-3001",
    customer_name: "Maya Patel",
    claim_type: "trip_delay",
    submitted_on: "2026-06-24",
    incident_date: "2026-06-18",
    incident_location: "Rome, Italy",
    summary: "Flight home canceled by the airline",
    story: "My flight home from Rome was canceled.",
    items: [
      { description: "Airport hotel", category: "accommodation", amount: 245 },
      { description: "Dinner and breakfast", category: "meals", amount: 95 },
      { description: "Taxis", category: "transport", amount: 80 },
    ],
    amount_claimed: 420,
    documents: [
      {
        name: "Hotel receipt",
        type: "receipt",
        content: "One night. Total paid: $245.00.",
      },
    ],
    status: "waiting",
    thread_id: null,
    decision: null,
    payment: null,
    ...overrides,
  };
}

export const policy: Policy = {
  policy_id: "POL-2001",
  plan: "premium",
  add_ons: ["electronics_plus"],
  purchased_on: "2026-04-22",
  trip: {
    destination: "Rome, Italy",
    departs_on: "2026-06-10",
    returns_on: "2026-06-18",
    trip_cost: 3100,
  },
  travelers: ["Maya Patel"],
  plan_details: { plan: "premium", name: "UnderCover Premium", deductible: 50 },
  add_on_details: [
    { add_on: "electronics_plus", name: "Electronics Plus", effect: "More." },
  ],
};

export const history: ClaimHistory = {
  customer_id: "CUS-3001",
  name: "Maya Patel",
  customer_since: "2023-04-11",
  previous_claims: [
    {
      claim_id: "CLM-0412",
      filed_on: "2024-08-19",
      claim_type: "baggage_delay",
      summary: "Checked bag arrived 30 hours late",
      outcome: "approved",
      amount_paid: 140,
    },
  ],
};

export function step(stepId: number, title: string, detail = "{}"): Step {
  return {
    step_id: stepId,
    kind: "tool",
    title,
    detail,
    created_at: "2026-11-02T12:07:49Z",
  };
}

export function claimRoutes(data: Claim, steps: Step[] = []): Routes {
  return {
    [`/api/claims/${data.claim_id}`]: data,
    [`/api/claims/${data.claim_id}/steps`]: steps,
    "/api/policies/POL-2001": policy,
    "/api/customers/CUS-3001/history": history,
  };
}
