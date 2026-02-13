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

async function populateRemoteCheckinForms(page: Page): Promise<void> {
  await page.evaluate(() => {
    const host = document.querySelector('app-remote-checkin');
    const ngRef = (window as any).ng;
    if (!host || !ngRef?.getComponent) {
      throw new Error('RemoteCheckin component instance not available');
    }

    const component = ngRef.getComponent(host);
    const now = new Date('2026-02-13T10:00:00.000Z');
    const expiry = new Date('2028-02-13T10:00:00.000Z');
    const birthday = new Date('1990-01-15T10:00:00.000Z');

    component.clientForm.patchValue({
      name: 'Mario',
      surname: 'Rossi',
      birthday,
      street: 'Via Roma',
      number_city: '10',
      cap: '00100',
      telephone: '3331234567',
      document_type: 'PASSPORT',
      document_number: 'YA1234567',
      cf: 'RSSMRA90A15H501U',
      sesso: '1',
      nazionalita: 'ITA',
      email: 'mario.rossi@example.com',
      comune_nascita_code: 'H501',
      provincia_nascita: 'RM',
      stato_nascita: 'ITA',
      cittadinanza: 'ITA',
      luogo_emissione: 'H501',
      data_emissione: now,
      data_scadenza: expiry,
      autorita_rilascio: 'Questura',
      comune_residenza_code: 'H501',
      provincia_residenza: 'RM',
      stato_residenza: 'ITA'
    });

    component.uploadForm.patchValue({
      frontimage: new File(['front'], 'front.jpg', { type: 'image/jpeg' }),
      backimage: new File(['back'], 'back.jpg', { type: 'image/jpeg' }),
      selfie: new File(['selfie'], 'selfie.jpg', { type: 'image/jpeg' })
    });

    component.clientForm.markAllAsTouched();
    component.uploadForm.markAllAsTouched();
    component.clientForm.updateValueAndValidity();
    component.uploadForm.updateValueAndValidity();
  });
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

    await expect(page.locator('.p-toast-message.p-toast-message-error')).toBeVisible();
  });

  test('create reservation submits and redirects to dashboard', async ({ page }) => {
    await seedAuthSession(page, 'admin', {
      selectedStructureId: '1',
      structures: [{ id: 1, name: 'Main Structure' }]
    });

    await page.route('**/api/v1/rooms**', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([{ id: 11, id_structure: 1, name: 'Room 11', capacity: 3, is_active: true }])
        });
        return;
      }
      await route.continue();
    });

    await page.route('**/api/v1/reservations', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 301, id_reference: 'RES301' })
      });
    });

    await page.goto('/admin/create-reservation');
    await page.evaluate(() => {
      const host = document.querySelector('app-create-reservation');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('CreateReservation component instance not available');
      }
      const component = ngRef.getComponent(host);
      component.reservationForm.patchValue({
        reservationNumber: 'RES301',
        startDate: new Date('2026-02-20T10:00:00.000Z'),
        endDate: new Date('2026-02-22T10:00:00.000Z'),
        roomName: { id: 11, id_structure: 1, name: 'Room 11', capacity: 3 },
        nameReference: 'Smoke Guest',
        email: 'smoke@example.com',
        telephone: '3331234567',
        numberOfPeople: 2
      });
      component.onSubmit();
    });

    await expect(page).toHaveURL(/\/admin\/dashboard/);
  });

  test('rooms page supports search and row status toggle only in edit mode', async ({ page }) => {
    await seedAuthSession(page, 'admin', {
      selectedStructureId: '1',
      structures: [{ id: 1, name: 'Main Structure' }]
    });

    let editCalls = 0;
    await page.route('**/api/v1/rooms**', async (route) => {
      const method = route.request().method();
      if (method === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 1, id_structure: 1, name: 'Blue Room', capacity: 2, is_active: true },
            { id: 2, id_structure: 1, name: 'Red Room', capacity: 4, is_active: true }
          ])
        });
        return;
      }
      if (method === 'PUT') {
        editCalls += 1;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: route.request().postData() || '{}'
        });
        return;
      }
      await route.continue();
    });

    await page.goto('/admin/rooms');
    await expect(page.getByText('Blue Room')).toBeVisible();
    await page.fill('#roomSearch', 'Blue');
    await expect(page.getByText('Blue Room')).toBeVisible();
    await expect(page.getByText('Red Room')).not.toBeVisible();

    const firstStatusPill = page.locator('.status-pill').first();
    await expect(firstStatusPill).toBeDisabled();
    await firstStatusPill.click({ force: true });
    expect(editCalls).toBe(0);

    await page.getByRole('button', { name: /edit/i }).first().click();
    await expect(firstStatusPill).toBeEnabled();
    await firstStatusPill.click();
    expect(editCalls).toBe(1);
  });

  test('remote check-in submit happy path redirects to completion page', async ({ page }) => {
    await page.route('**/api/v1/reservations/check/123', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 123,
          number_of_people: 2,
          registered_clients_count: 0,
          upload_token: 'smoke-upload-token'
        })
      });
    });

    await page.route('**/api/v1/upload', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Upload completed' })
      });
    });

    await page.goto('/123/remote-checkin/en');
    await populateRemoteCheckinForms(page);
    await page.evaluate(() => {
      const host = document.querySelector('app-remote-checkin');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('RemoteCheckin component instance not available');
      }
      const component = ngRef.getComponent(host);
      component.reservationId = '123';
      component.canRegister = true;
      component.uploadToken = 'smoke-upload-token';
      component.uploadReservationData();
    });

    await expect(page).toHaveURL(/\/checkin-complete\/123/);
  });

  test('remote check-in shows localized error when upload token is missing', async ({ page }) => {
    await page.route('**/api/v1/reservations/check/124', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 124,
          number_of_people: 2,
          registered_clients_count: 0,
          upload_token: null
        })
      });
    });

    await page.goto('/124/remote-checkin/en');
    await populateRemoteCheckinForms(page);
    await page.evaluate(() => {
      const host = document.querySelector('app-remote-checkin');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('RemoteCheckin component instance not available');
      }
      const component = ngRef.getComponent(host);
      component.reservationId = '124';
      component.canRegister = true;
      component.uploadToken = null;
      component.uploadReservationData();
    });

    await expect(page.getByText('Unable to continue: upload security token missing. Please refresh and try again.')).toBeVisible();
  });

  test('landing header language switch updates translated labels', async ({ page }) => {
    await page.goto('/landing');
    await expect(page.locator('.header__signin')).toHaveText('Sign in');

    await page.hover('.language-menu');
    await page.click('.language-menu__list button:has-text("Italiano")');

    await expect(page.locator('.header__signin')).toHaveText('Accedi');
  });
});
