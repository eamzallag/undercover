import { expect, test } from "@playwright/test";

test("the queue shows every claim and where it stands", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Claims queue" }),
  ).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(25);

  const row = page.getByRole("row").filter({ hasText: "CLM-1001" });
  await expect(row).toContainText("Maya Patel");
  await expect(row).toContainText("Trip delay");
  await expect(row).toContainText("$420.00");
  await expect(row).toContainText("Waiting");
});
