import { act, cleanup, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, expect, it, vi } from "vitest";
import { REFRESH_MS } from "./api";
import { QueuePage } from "./QueuePage";
import { stubApi, summary } from "./testing";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

function renderQueue() {
  render(
    <MemoryRouter>
      <QueuePage />
    </MemoryRouter>,
  );
}

const queue = [
  summary({}),
  summary({
    claim_id: "CLM-1002",
    customer_name: "Ana Souza",
    claim_type: "baggage",
    amount_claimed: 1150,
    status: "waiting_for_sign_off",
    decision: "approve",
    payout: 1100,
  }),
  summary({
    claim_id: "CLM-1003",
    claim_type: "emergency_medical",
    status: "decided",
    decision: "decline",
    payout: 0,
  }),
];

it("shows each claim with where it stands", async () => {
  stubApi({ "/api/claims": queue });
  renderQueue();

  const link = await screen.findByRole("link", { name: "CLM-1002" });
  expect(link.getAttribute("href")).toBe("/claims/CLM-1002");
  const row = link.closest("tr");
  if (!row) throw new Error("no row");
  const cells = within(row);
  expect(cells.getByText("Ana Souza")).toBeDefined();
  expect(cells.getByText("Baggage")).toBeDefined();
  expect(cells.getByText("$1,150.00")).toBeDefined();
  expect(cells.getByText("$1,100.00")).toBeDefined();
  expect(cells.getByText("Waiting for sign-off")).toBeDefined();
  expect(cells.getByText("Approved")).toBeDefined();
  expect(screen.getByText("Emergency medical")).toBeDefined();
  expect(screen.getByText("Declined")).toBeDefined();
});

it("counts the claims in each status", async () => {
  stubApi({ "/api/claims": queue });
  renderQueue();

  expect((await screen.findByLabelText("Waiting count")).textContent).toBe("1");
  expect(screen.getByLabelText("In progress count").textContent).toBe("0");
  expect(screen.getByLabelText("Waiting for sign-off count").textContent).toBe(
    "1",
  );
  expect(screen.getByLabelText("Decided count").textContent).toBe("1");
});

it("picks up a change on the next refresh", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  const routes = { "/api/claims": [summary({})] };
  stubApi(routes);
  renderQueue();
  expect((await screen.findByLabelText("Waiting count")).textContent).toBe("1");

  routes["/api/claims"] = [summary({ status: "in_progress" })];
  await act(() => vi.advanceTimersByTimeAsync(REFRESH_MS));

  expect(screen.getByLabelText("In progress count").textContent).toBe("1");
  expect(screen.getByLabelText("Waiting count").textContent).toBe("0");
});

it("says when the backend isn't responding", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  renderQueue();
  expect(await screen.findByText(/The backend isn't responding/)).toBeDefined();
});
