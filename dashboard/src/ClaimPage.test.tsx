import { act, cleanup, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, expect, it, vi } from "vitest";
import { REFRESH_MS } from "./api";
import { ClaimPage } from "./ClaimPage";
import { claim, claimRoutes, step, stubApi } from "./testing";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

function renderClaim(claimId = "CLM-1001") {
  render(
    <MemoryRouter initialEntries={[`/claims/${claimId}`]}>
      <Routes>
        <Route path="/claims/:claimId" element={<ClaimPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

const decision = {
  decision: "approve" as const,
  payout: 1100,
  reasons: "The bag was lost by the airline.",
  policy_section: "Section 5, Baggage and Personal Effects",
  decided_at: "2026-11-02T12:07:49Z",
};

it("shows a waiting claim in full", async () => {
  stubApi(claimRoutes(claim({})));
  renderClaim();

  expect(
    await screen.findByText("My flight home from Rome was canceled."),
  ).toBeDefined();
  expect(screen.getByRole("heading", { name: "CLM-1001" })).toBeDefined();
  expect(screen.getByText("Airport hotel")).toBeDefined();
  expect(screen.getAllByText("$420.00")).toHaveLength(2);
  expect(screen.getByText("One night. Total paid: $245.00.")).toBeDefined();
  expect(
    screen.getByText("The agent hasn't worked this claim yet."),
  ).toBeDefined();
  expect(await screen.findByText("No steps yet.")).toBeDefined();
  expect(await screen.findByText("UnderCover Premium")).toBeDefined();
  expect(screen.getByText("Electronics Plus")).toBeDefined();
  expect(await screen.findByText("CLM-0412")).toBeDefined();
});

it("shows new steps while the agent works", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  const working = claim({ status: "in_progress", thread_id: "CLM-1001-ab12" });
  const routes = claimRoutes(working);
  stubApi(routes);
  renderClaim();

  expect(await screen.findByText("Starting...")).toBeDefined();
  expect(screen.getByText("CLM-1001-ab12")).toBeDefined();
  expect(screen.getByText("The agent is working on this claim.")).toBeDefined();

  routes["/api/claims/CLM-1001/steps"] = [
    step(1, "Reading the claim", '{"claim_id":"CLM-1001"}'),
    {
      ...step(2, "The agent's note"),
      kind: "message",
      detail: "Next, the policy.",
    },
  ];
  await act(() => vi.advanceTimersByTimeAsync(REFRESH_MS));

  const steps = screen.getByRole("region", { name: "The agent's steps" });
  const items = await within(steps).findAllByRole("listitem");
  expect(items[0]?.textContent).toContain("Reading the claim");
  expect(items[1]?.textContent).toContain("Next, the policy.");
  expect(screen.getByText(/"claim_id": "CLM-1001"/)).toBeDefined();
});

it("shows a payment waiting for sign-off", async () => {
  stubApi(
    claimRoutes(claim({ status: "waiting_for_sign_off", decision }), [
      step(1, "Recording the decision"),
    ]),
  );
  renderClaim();

  expect(
    await screen.findByText(
      "Payment of $1,100.00 waits for a handler's sign-off.",
    ),
  ).toBeDefined();
  expect(screen.getByText("Approved")).toBeDefined();
  expect(screen.getByText("$1,100.00")).toBeDefined();
  expect(screen.getByText("The bag was lost by the airline.")).toBeDefined();
  expect(
    screen.getByText("Section 5, Baggage and Personal Effects"),
  ).toBeDefined();
  expect(await screen.findByText("Recording the decision")).toBeDefined();
});

it("shows who signed off a payment", async () => {
  const payment = {
    amount: 1100,
    paid_at: "2026-11-02T13:00:00Z",
    signed_off_by: "Dana Whitfield",
  };
  stubApi(claimRoutes(claim({ status: "decided", decision, payment })));
  renderClaim();

  expect(await screen.findByText(/Paid \$1,100.00 on/)).toBeDefined();
  expect(screen.getByText(/signed off by Dana Whitfield/)).toBeDefined();
});

it("shows an approval that isn't paid yet", async () => {
  stubApi(claimRoutes(claim({ status: "decided", decision })));
  renderClaim();
  expect(await screen.findByText("Not paid yet.")).toBeDefined();
});

it("shows a decline without a payout", async () => {
  const declined = { ...decision, decision: "decline" as const, payout: 0 };
  stubApi(claimRoutes(claim({ status: "decided", decision: declined })));
  renderClaim();

  expect(await screen.findByText("Declined")).toBeDefined();
  expect(screen.queryByText("$0.00")).toBeNull();
  expect(screen.queryByText(/Paid|Not paid/)).toBeNull();
});

it("says when a claim doesn't exist", async () => {
  stubApi({});
  renderClaim("CLM-9999");
  expect(
    await screen.findByRole("heading", { name: "Claim not found" }),
  ).toBeDefined();
});

it("says when the backend isn't responding", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  renderClaim();
  expect(await screen.findByText(/The backend isn't responding/)).toBeDefined();
});
