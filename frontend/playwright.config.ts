import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry"
  },
  webServer: {
    command: "npm run dev",
    port: 3000,
    reuseExistingServer: true,
    env: {
      NEXT_PUBLIC_E2E_MOCK: "true",
      NEXT_PUBLIC_API_BASE_URL: "http://localhost:8000"
    }
  }
});
