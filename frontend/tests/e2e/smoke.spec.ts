import { expect, test } from '@playwright/test';

test.describe('Frontend smoke', () => {
  test('landing page renders core sections and CTA links', async ({ page }) => {
    await page.goto('/landing');
    await expect(page.locator('app-header .app-header')).toBeVisible();
    await expect(page.locator('section.hero')).toBeVisible();
    await expect(page.locator('section.features')).toBeVisible();

    const pricingCta = page.locator('.hero__cta .btn--primary');
    const loginCta = page.locator('.hero__cta .btn--ghost');

    await expect(pricingCta).toBeVisible();
    await expect(loginCta).toBeVisible();
    await expect(pricingCta).toHaveAttribute('href', '/pricing');
    await expect(loginCta).toHaveAttribute('href', '/admin/login');
  });

  test('admin login page renders expected form controls', async ({ page }) => {
    await page.goto('/admin/login');
    await expect(page.locator('form')).toBeVisible();
    await expect(page.locator('#username')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.locator('button[type="submit"]').first()).toBeVisible();
  });

  test('pricing page renders plan section', async ({ page }) => {
    await page.goto('/pricing');
    await expect(page.locator('app-header .app-header')).toBeVisible();
    await expect(page.locator('.pricing')).toBeVisible();
    await expect(page.locator('.plans')).toBeVisible();
  });
});
