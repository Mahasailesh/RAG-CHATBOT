import path from "node:path";
import { test, expect } from "@playwright/test";

test("audit flow from upload to report", async ({ page }) => {
  await page.goto("/");

  const filePath = path.join(__dirname, "fixtures", "sample.pdf");
  await page.setInputFiles('input[type="file"]', filePath);

  await expect(page.getByText("sample.pdf")).toBeVisible();

  await page.route("**/api/audit", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "issues_found",
        issues: [
          {
            category: "date",
            field: "expiry_date",
            expected: "2030-01-01",
            found: "2029-01-01",
            page: 1,
            severity: "high",
            notes: "Mismatch"
          }
        ],
        summary: "One discrepancy detected."
      })
    });
  });

  await page.getByRole("button", { name: "Run audit" }).click();

  await expect(page.getByText("1 issues found")).toBeVisible();
  await expect(page.getByText("expiry_date")).toBeVisible();
});
