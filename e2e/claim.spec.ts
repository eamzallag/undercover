import { expect, test } from "@playwright/test";

test("a claim opens from the queue in full", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "CLM-1001" }).click();

  await expect(page).toHaveURL(/\/claims\/CLM-1001$/);
  await expect(page.getByText(/My flight home from Rome/)).toBeVisible();
  const items = page.getByRole("region", { name: "Items" });
  await expect(items.getByRole("row")).toHaveCount(5);
  await expect(items.getByRole("row", { name: /Total/ })).toContainText(
    "$420.00",
  );
  const documents = page.getByRole("region", { name: "Documents" });
  await expect(documents.getByRole("article")).toHaveCount(4);
  await expect(page.getByText("UnderCover Premium")).toBeVisible();
  await expect(page.getByText("CLM-0412")).toBeVisible();
});

test("the claim page shows the agent's work", async ({ page, request }) => {
  const claim = "/api/claims/CLM-1002";
  await request.post(`${claim}/start`, { data: { thread_id: "e2e-1" } });
  for (const title of ["Reading the claim", "Reading the policy"]) {
    await request.post(`${claim}/steps`, {
      data: { kind: "tool", title, detail: "{}" },
    });
  }
  await request.post(`${claim}/decision`, {
    data: {
      decision: "approve",
      payout: 1100,
      reasons: "The suitcase was lost by the airline.",
      policy_section: "Section 5, Baggage and Personal Effects",
    },
  });

  await page.goto("/claims/CLM-1002");
  await expect(page.getByText("Waiting for sign-off").first()).toBeVisible();
  await expect(
    page.getByText("The suitcase was lost by the airline."),
  ).toBeVisible();
  await expect(
    page.getByText("Section 5, Baggage and Personal Effects"),
  ).toBeVisible();
  const steps = page.getByRole("region", { name: "The agent's steps" });
  await expect(steps.getByRole("listitem")).toHaveCount(2);
  await expect(steps.getByRole("listitem").first()).toContainText(
    "Reading the claim",
  );
  await expect(steps.getByRole("listitem").last()).toContainText(
    "Reading the policy",
  );
  await expect(
    page.getByText("Payment of $1,100.00 waits for a handler's sign-off."),
  ).toBeVisible();

  await page.getByRole("link", { name: "Queue" }).click();
  const row = page.getByRole("row").filter({ hasText: "CLM-1002" });
  await expect(row).toContainText("Waiting for sign-off");
});

test("an unknown claim says so", async ({ page }) => {
  await page.goto("/claims/CLM-9999");
  await expect(
    page.getByRole("heading", { name: "Claim not found" }),
  ).toBeVisible();
});
