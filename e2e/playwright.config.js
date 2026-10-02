// Runs against `docker compose up` (web :8080, API :8000, Mailpit :8025), never production.
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  workers: 1, // the demo accounts are shared state
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : 'list',
  // A deployed free tier (E2E_BASE_URL) has cold database compute; give it time.
  expect: { timeout: process.env.E2E_BASE_URL ? 15_000 : 5_000 },
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:8080',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
