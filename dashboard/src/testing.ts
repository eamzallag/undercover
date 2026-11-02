import { vi } from "vitest";
import type { ClaimSummary } from "./api";

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
