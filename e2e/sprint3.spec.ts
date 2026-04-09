import { test, expect, type Page } from '@playwright/test';

async function loginAsAdmin(page: Page) {
  const email = process.env.E2E_USER_EMAIL || 'admin@e2e.local';
  const password = process.env.E2E_USER_PASSWORD || 'E2ePass123!';
  await page.goto('/login/');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Login' }).click();
  await expect(page).toHaveURL(/\/(dashboard)?$/);
}

test.describe('Sprint 3 core flows', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('route planner page is reachable', async ({ page }) => {
    await page.goto('/routes/');
    await expect(page).toHaveURL(/\/routes\/$/);
    await expect(page.locator('body')).toContainText(/route|ruta|planner|planificador/i);
  });

  test('spare parts inventory page is reachable', async ({ page }) => {
    await page.goto('/inventory/');
    await expect(page).toHaveURL(/\/inventory\/$/);
    await expect(page.locator('body')).toContainText(/spare part|inventory|repuesto|inventario/i);
  });

  test('suppliers page is reachable', async ({ page }) => {
    await page.goto('/inventory/suppliers/');
    await expect(page).toHaveURL(/\/inventory\/suppliers\/$/);
    await expect(page.locator('body')).toContainText(/supplier|proveedor/i);
  });

  test('dashboard customize page is reachable', async ({ page }) => {
    await page.goto('/dashboard/customize/');
    await expect(page).toHaveURL(/\/dashboard\/customize\/$/);
    await expect(page.locator('body')).toContainText(/customize|layout|widget|personalizar/i);
  });
});
