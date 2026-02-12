import { test, expect } from '@playwright/test';

test.describe('Navigation when logged in', () => {
  test.beforeEach(async ({ page }) => {
    const email = process.env.E2E_USER_EMAIL || 'admin@e2e.local';
    const password = process.env.E2E_USER_PASSWORD || 'E2ePass123!';
    await page.goto('/login/');
    await page.getByLabel('Email').fill(email);
    await page.getByLabel('Password').fill(password);
    await page.getByRole('button', { name: 'Login' }).click();
    await expect(page).toHaveURL(/\/(dashboard)?$/);
  });

  test('Dashboard shows key sections', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Dashboard')).toBeVisible();
    await expect(page.getByText('Total Vehicles').or(page.getByText('Fleet Availability'))).toBeVisible();
  });

  test('Vehicles link goes to vehicle list', async ({ page }) => {
    await page.getByRole('link', { name: 'Vehicles' }).first().click();
    await expect(page).toHaveURL(/\/vehicles\/$/);
    await expect(page.getByText(/vehicles|license plate/i)).toBeVisible();
  });

  test('Maintenance link goes to task list', async ({ page }) => {
    await page.getByRole('link', { name: 'Maintenance' }).first().click();
    await expect(page).toHaveURL(/\/maintenance\/$/);
    await expect(page.getByText(/maintenance|task/i)).toBeVisible();
  });

  test('Alerts link goes to alerts page', async ({ page }) => {
    await page.getByRole('link', { name: 'Alerts' }).first().click();
    await expect(page).toHaveURL(/\/alerts\/$/);
    await expect(page.getByText(/alert|notification/i)).toBeVisible();
  });

  test('Reports link goes to reports index', async ({ page }) => {
    await page.getByRole('link', { name: 'Reports' }).first().click();
    await expect(page).toHaveURL(/\/reports\/$/);
    await expect(page.getByText(/report|fleet|download/i)).toBeVisible();
  });
});
