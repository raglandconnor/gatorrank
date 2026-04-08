import { expect, test } from '@playwright/test';

test('home renders sections and allows navigating to login', async ({
  page,
}) => {
  await page.goto('/');

  await expect(page.getByText('Top Overall UF Projects')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Sign Up' })).toBeVisible();

  const loginLink = page.getByRole('link', { name: 'Log In' });
  await expect(loginLink).toBeVisible();
  await loginLink.click();

  await expect(page).toHaveURL(/\/login/);
  await expect(
    page.getByRole('heading', { name: 'Welcome Back' }),
  ).toBeVisible();
});
