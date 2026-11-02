import { defineConfig } from "@playwright/test";

// The end-to-end run has its own backend, database and dashboard, seeded fresh,
// so it never changes the data that `npm run dev` uses.
export default defineConfig({
  testDir: "e2e",
  outputDir: "e2e/test-results",
  reporter: "list",
  use: { baseURL: "http://localhost:5174" },
  webServer: [
    {
      command:
        "uv run -m backend.seed && uv run -m uvicorn backend.main:app --port 8765",
      url: "http://127.0.0.1:8765/api/health",
      env: { UNDERCOVER_DB: "e2e/undercover-e2e.db" },
      reuseExistingServer: false,
    },
    {
      command: "npx vite dashboard --port 5174 --strictPort",
      url: "http://localhost:5174",
      env: { UNDERCOVER_API: "http://127.0.0.1:8765" },
      reuseExistingServer: false,
    },
  ],
});
