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
    await expect(page.locator('body')).toContainText(/dashboard|panel/i);
    await expect(page.getByText(/total vehicles|fleet availability|vehiculos totales|disponibilidad/i).first()).toBeVisible();
  });

  test('Vehicles link goes to vehicle list', async ({ page }) => {
    await page.goto('/vehicles/');
    await expect(page).toHaveURL(/\/vehicles\/$/);
    await expect(page.getByRole('heading', { name: /vehicles|vehiculos/i })).toBeVisible();
  });

  test('Maintenance link goes to task list', async ({ page }) => {
    await page.goto('/maintenance/');
    await expect(page).toHaveURL(/\/maintenance\/$/);
    await expect(page.getByRole('heading', { name: /maintenance|mantenimiento/i })).toBeVisible();
  });

  test('Alerts link goes to alerts page', async ({ page }) => {
    await page.goto('/alerts/');
    await expect(page).toHaveURL(/\/alerts\/$/);
    await expect(page.getByRole('heading', { name: /alerts|alertas/i })).toBeVisible();
  });

  test('Reports link goes to reports index', async ({ page }) => {
    await page.goto('/reports/');
    await expect(page).toHaveURL(/\/reports\/$/);
    await expect(page.locator('body')).toContainText(/reports|reportes/i);
  });
});
