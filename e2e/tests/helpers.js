import { expect } from '@playwright/test';

export const MAILPIT = process.env.E2E_MAILPIT_URL ?? 'http://localhost:8025';

export const DEMO = {
  teacher: { email: 'demo.teacher@example.com', password: 'skillswap-demo-1', name: 'Demo Teacher' },
  learner: { email: 'demo.learner@example.com', password: 'skillswap-demo-2', name: 'Demo Learner' },
};

export const uniqueEmail = (tag) => `${tag}.${Date.now()}.${Math.floor(Math.random() * 1e6)}@example.com`;

export async function signIn(page, { email, password }) {
  await page.goto('/');
  await page.getByRole('tab', { name: 'Sign in' }).click();
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByText('Signed in as')).toBeVisible();
}

export async function signOut(page) {
  await page.getByRole('button', { name: 'Sign out' }).click();
  await expect(page.getByRole('tab', { name: 'Sign in' })).toBeVisible();
}

// Wait for the newest mail to `to` in Mailpit and return the first link with a token.
export async function linkFromMail(request, to, subjectWord) {
  let link = null;
  await expect
    .poll(async () => {
      const search = await request.get(`${MAILPIT}/api/v1/search`, {
        params: { query: `to:"${to}" subject:"${subjectWord}"` },
      });
      const [newest] = (await search.json()).messages ?? [];
      if (!newest) return null;
      const message = await (await request.get(`${MAILPIT}/api/v1/message/${newest.ID}`)).json();
      link = message.Text.match(/https?:\/\/\S+token=[\w-]+/)?.[0] ?? null;
      return link;
    }, { timeout: 15_000 })
    .not.toBeNull();
  return new URL(link).pathname + new URL(link).search;
}

export async function register(page, { name, email, password }) {
  await page.goto('/');
  await page.getByRole('tab', { name: 'Create account' }).click();
  await page.getByLabel('Name').fill(name);
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page.getByRole('status')).toContainText('Check your email');
}
