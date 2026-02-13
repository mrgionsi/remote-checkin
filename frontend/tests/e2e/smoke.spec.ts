import { expect, test, type Page } from '@playwright/test';

function buildFakeJwt(expirationOffsetSeconds = 3600): string {
  const payload = {
    exp: Math.floor(Date.now() / 1000) + expirationOffsetSeconds
  };
  return `header.${Buffer.from(JSON.stringify(payload)).toString('base64url')}.signature`;
}

async function seedAuthSession(
  page: Page,
  role: 'admin' | 'superadmin',
  options?: { selectedStructureId?: string | null; structures?: Array<{ id: number; name: string }> }
): Promise<void> {
  const token = buildFakeJwt();
  const selectedStructureId = options?.selectedStructureId === undefined ? '1' : options.selectedStructureId;
  const structures = options?.structures ?? [{ id: 1, name: 'Smoke Structure' }];
  await page.addInitScript(({ authToken, authRole, structureId, structureList }) => {
    localStorage.setItem('admin_token', authToken);
    localStorage.setItem('appLang', 'en');
    localStorage.setItem('remote-checkin-lang', 'en');
    if (structureId) {
      localStorage.setItem('selected_structure_id', structureId);
    } else {
      localStorage.removeItem('selected_structure_id');
    }
    localStorage.setItem('user', JSON.stringify({
      id: 1,
      username: 'smoke-admin',
      role: authRole,
      structures: structureList
    }));
  }, { authToken: token, authRole: role, structureId: selectedStructureId, structureList: structures });
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
    await seedAuthSession(page, 'admin');

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

  test('auth guard redirects unauthenticated access from dashboard to login', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.removeItem('admin_token');
      localStorage.removeItem('user');
      localStorage.removeItem('selected_structure_id');
    });

    await page.goto('/admin/dashboard');
    await expect(page).toHaveURL(/\/admin\/login/);
    await expect(page.locator('form')).toBeVisible();
  });

  test('dashboard shows no-structure state when selected_structure_id is missing', async ({ page }) => {
    await seedAuthSession(page, 'admin', {
      selectedStructureId: null,
      structures: []
    });

    let reservationCalls = 0;
    let monthlyCalls = 0;
    await page.route('**/api/v1/reservations/structure/*', async (route) => {
      reservationCalls += 1;
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });
    await page.route('**/api/v1/reservations/monthly/*', async (route) => {
      monthlyCalls += 1;
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([{ total_reservations: 0 }]) });
    });

    await page.goto('/admin/dashboard');
    await expect(page).toHaveURL(/\/admin\/dashboard/);
    await page.waitForTimeout(300);
    expect(reservationCalls).toBe(0);
    expect(monthlyCalls).toBe(0);
    await expect(page.locator('.stats-grid')).toBeVisible();
  });

  test('reservation details redirects to dashboard when reservation belongs to another structure', async ({ page }) => {
    await seedAuthSession(page, 'admin', {
      selectedStructureId: '1',
      structures: [{ id: 1, name: 'Main Structure' }]
    });

    await page.route('**/api/v1/reservations/admin/127', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 127,
          id_reference: 'RES-127',
          name_reference: 'Other Structure Guest',
          status: 'Pending',
          room: {
            id: 30,
            id_structure: 2,
            name: 'Room X'
          }
        })
      });
    });
    await page.route('**/api/v1/rooms**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });
    await page.route('**/api/v1/reservations/structure/*', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });
    await page.route('**/api/v1/reservations/monthly/*', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([{ total_reservations: 0 }]) });
    });

    await page.goto('/admin/reservation-details/127');
    await expect(page).toHaveURL(/\/admin\/dashboard/);
  });

  test('superadmin route is denied for admin role and allowed for superadmin role', async ({ page }) => {
    await seedAuthSession(page, 'admin');
    await page.route('**/api/v1/reservations/structure/*', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });
    await page.route('**/api/v1/reservations/monthly/*', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([{ total_reservations: 0 }]) });
    });

    await page.goto('/admin/superadmin/dashboard');
    await expect(page).toHaveURL(/\/admin\/dashboard/);

    await seedAuthSession(page, 'superadmin', {
      selectedStructureId: null,
      structures: []
    });
    await page.route('**/api/v1/superadmin/dashboard', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          dashboard: {
            total_structures: 1,
            active_structures: 1,
            archived_structures: 0,
            total_users: 1,
            unassigned_admins: 0,
            total_reservations: 5
          }
        })
      });
    });

    await page.goto('/admin/superadmin/dashboard');
    await expect(page).toHaveURL(/\/admin\/superadmin\/dashboard/);
    await expect(page.locator('.dashboard')).toBeVisible();
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
