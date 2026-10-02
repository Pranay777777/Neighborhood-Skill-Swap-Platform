import { test, expect } from '@playwright/test';
import { DEMO, linkFromMail, register, signIn, signOut, uniqueEmail } from './helpers';

test('anonymous visitors see the board but not contact details', async ({ page }) => {
  await page.goto('/');
  const card = page.getByRole('article', { name: 'Guitar Lessons' });
  await expect(card).toBeVisible();
  await expect(card.getByText(DEMO.teacher.email)).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Share Your Skills' })).toHaveCount(0);
});

test('demo account signs in, posts a skill, comments and deletes it', async ({ page }) => {
  await signIn(page, DEMO.teacher);
  const title = `Bread baking ${Date.now()}`;
  await page.getByPlaceholder('e.g., Piano, Coding, Cooking, Gardening').fill(title);
  await page.getByPlaceholder(/Tell us more/).fill('Sourdough basics on Sunday mornings.');
  await page.getByRole('button', { name: 'Add to Skill Board' }).click();

  const card = page.getByRole('article', { name: title });
  await expect(card).toBeVisible();
  await card.getByRole('button', { name: 'Leave a comment' }).click();
  await card.getByLabel('Comment').fill('Bring your own flour.');
  await card.getByRole('button', { name: 'Post Comment' }).click();
  await expect(card.getByText('Bring your own flour.')).toBeVisible();
  await expect(card.getByRole('button', { name: '1 comment' })).toBeVisible(); // saved and reloaded

  await card.getByRole('button', { name: `Delete ${title}` }).click();
  await expect(card).toHaveCount(0);
});

test('a swap request is private to the requester and the skill owner', async ({ page, request }) => {
  const message = `Swap for Spanish? ${Date.now()}`;
  await signIn(page, DEMO.learner);
  const guitar = page.getByRole('article', { name: 'Guitar Lessons' });
  await guitar.getByLabel('Swap request for Guitar Lessons').fill(message);
  await guitar.getByRole('button', { name: 'Request' }).click();
  await expect(guitar.getByRole('status')).toContainText('only Demo Teacher can see it');
  await signOut(page);

  await signIn(page, DEMO.teacher);
  const inbox = page.getByRole('region', { name: 'My swap requests' });
  const item = inbox.getByRole('listitem').filter({ hasText: message });
  await expect(item).toBeVisible();
  await item.getByRole('button', { name: 'Accept' }).click();
  await expect(item).toContainText('accepted');
  await signOut(page);

  // A third neighbour never sees it (the API-level IDOR tests live in backend/tests/test_authz.py).
  const outsider = { name: 'Outsider', email: uniqueEmail('outsider'), password: 'outsider-password-1' };
  await register(page, outsider);
  await page.goto(await linkFromMail(request, outsider.email, 'Verify'));
  await signIn(page, outsider);
  await expect(page.getByText(message)).toHaveCount(0);
});

test('register, verify by email link, then post', async ({ page, request }) => {
  const user = { name: 'New Neighbour', email: uniqueEmail('new'), password: 'a-long-enough-pw' };
  await register(page, user);
  await signIn(page, user);
  await expect(page.getByText('Verify your email to post')).toBeVisible();

  await page.goto(await linkFromMail(request, user.email, 'Verify'));
  await expect(page.getByRole('status')).toContainText('Email verified');
  // still signed in from before; the reload picks up the verified status
  await page.goto('/');
  await expect(page.getByText('Signed in as')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Share Your Skills' })).toBeVisible();
});

test('password reset by email link signs in with the new password only', async ({ page, request }) => {
  const user = { name: 'Forgetful', email: uniqueEmail('reset'), password: 'the-old-password' };
  await register(page, user);
  await page.getByRole('tab', { name: 'Forgot password' }).click();
  await page.getByLabel('Email').fill(user.email);
  await page.getByRole('button', { name: 'Forgot password' }).click();
  await expect(page.getByRole('status')).toContainText('If that email is registered');

  const link = await linkFromMail(request, user.email, 'Reset');
  await page.goto(link);
  await page.getByLabel('New password').fill('the-new-password');
  await page.getByRole('button', { name: 'Save password' }).click();
  await expect(page.getByRole('status')).toContainText('Password changed');

  // the link is single-use
  await page.goto(link);
  await page.getByLabel('New password').fill('a-third-password');
  await page.getByRole('button', { name: 'Save password' }).click();
  await expect(page.getByRole('alert')).toContainText('Invalid or expired');

  await signIn(page, { ...user, password: 'the-new-password' });
});
