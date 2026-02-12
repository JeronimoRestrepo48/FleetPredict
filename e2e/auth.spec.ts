import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('login page loads and shows FleetPredict', async ({ page }) => {
    await page.goto('/login/');
    await expect(page).toHaveTitle(/FleetPredict/);
    await expect(page.getByLabel('Email')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Login' })).toBeVisible();
  });

  test('login with valid credentials redirects to dashboard', async ({ page }) => {
    const email = process.env.E2E_USER_EMAIL || 'admin@e2e.local';
    const password = process.env.E2E_USER_PASSWORD || 'E2ePass123!';
    await page.goto('/login/');
    await page.getByLabel('Email').fill(email);
    await page.getByLabel('Password').fill(password);
    await page.getByRole('button', { name: 'Login' }).click();
    await expect(page).toHaveURL(/\/(dashboard)?$/);
    await expect(page.getByText('Dashboard')).toBeVisible();
  });
});
