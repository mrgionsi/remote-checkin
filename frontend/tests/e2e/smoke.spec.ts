import { expect, test } from '@playwright/test';

function buildFakeJwt(expirationOffsetSeconds = 3600): string {
  const payload = {
    exp: Math.floor(Date.now() / 1000) + expirationOffsetSeconds
  };
  return `header.${Buffer.from(JSON.stringify(payload)).toString('base64url')}.signature`;
}

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

  test('admin dashboard renders for an authenticated session', async ({ page }) => {
    await page.addInitScript(({ token }) => {
      localStorage.setItem('admin_token', token);
      localStorage.setItem('selected_structure_id', '1');
      localStorage.setItem('user', JSON.stringify({
        id: 1,
        username: 'smoke-admin',
        role: 'admin',
        structures: [{ id: 1, name: 'Smoke Structure' }]
      }));
    }, { token: buildFakeJwt() });

    await page.route('**/api/v1/reservations/structure/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{
          reservation_id: 101,
          name_reference: 'Smoke Guest',
          room_name: 'Room A',
          start_date: '2026-02-10',
          end_date: '2026-02-12',
          status: 'Pending',
          id_reference: 'SMK101'
        }])
      });
    });

    await page.route('**/api/v1/reservations/monthly/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ total_reservations: 1 }])
      });
    });

    await page.goto('/admin/dashboard');
    await expect(page).toHaveURL(/\/admin\/dashboard/);
    await expect(page.locator('.stats-grid')).toBeVisible();
    await expect(page.locator('p-table')).toBeVisible();
  });

  test('admin login shows error toast on invalid credentials', async ({ page }) => {
    await page.route('**/api/v1/admin/login', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Invalid credentials' })
      });
    });

    await page.goto('/admin/login');
    await page.fill('#username', 'wrong-user');
    await page.fill('#password', 'wrong-password');
    await page.click('button[type="submit"]');

    await expect(page.getByText(/username o password errati/i)).toBeVisible();
  });
});
