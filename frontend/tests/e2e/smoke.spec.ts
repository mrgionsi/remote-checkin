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

  test('remote check-in blocks registration when reservation is at full capacity', async ({ page }) => {
    await page.goto('/126/remote-checkin/en');
    await page.evaluate(() => {
      const host = document.querySelector('app-remote-checkin');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('RemoteCheckin component instance not available');
      }
      const component = ngRef.getComponent(host);
      component.reservationDetails = {
        id: 126,
        number_of_people: 1,
        registered_clients_count: 1,
        upload_token: 'capacity-full-token'
      };
      component.checkRegistrationCapacity();
    });

    await expect(page.getByRole('alert').getByText('Registration Full')).toBeVisible();
    await expect(page.locator('#name').first()).toBeDisabled();
    await expect(page.locator('button.p-button:has(.pi-arrow-right)').first()).toBeDisabled();
  });

  test('remote check-in shows warning when reservation check fails', async ({ page }) => {
    await page.route('**/api/v1/reservations/check/127', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });

    await page.goto('/127/remote-checkin/en');
    await expect(page.getByText('Registration Unavailable')).toBeVisible();
    await expect(page.getByText('Unable to verify reservation capacity. Registration is temporarily disabled.')).toBeVisible();
    await expect(page.locator('#name').first()).toBeDisabled();
  });

  test('remote check-in submit shows validation error on incomplete form', async ({ page }) => {
    await page.route('**/api/v1/reservations/check/128', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 128,
          number_of_people: 2,
          registered_clients_count: 0,
          upload_token: 'validation-token'
        })
      });
    });

    await page.goto('/128/remote-checkin/en');
    await page.evaluate(() => {
      const host = document.querySelector('app-remote-checkin');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('RemoteCheckin component instance not available');
      }
      const component = ngRef.getComponent(host);
      component.uploadReservationData();
    });

    await expect(page.getByText('All fields and images are required')).toBeVisible();
  });

  test('remote check-in submit shows API validation error message', async ({ page }) => {
    await page.route('**/api/v1/reservations/check/129', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 129,
          number_of_people: 2,
          registered_clients_count: 0,
          upload_token: 'upload-error-token'
        })
      });
    });

    await page.route('**/api/v1/upload', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Missing one or more required image files' })
      });
    });

    await page.goto('/129/remote-checkin/en');
    await populateRemoteCheckinForms(page);
    await page.evaluate(() => {
      const host = document.querySelector('app-remote-checkin');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('RemoteCheckin component instance not available');
      }
      const component = ngRef.getComponent(host);
      component.reservationId = '129';
      component.canRegister = true;
      component.uploadToken = 'upload-error-token';
      component.uploadReservationData();
    });

    await expect(page.getByText('Missing one or more required image files')).toBeVisible();
  });

  test('remote check-in restores non-PII draft within TTL and expires stale draft', async ({ page }) => {
    await page.route('**/api/v1/reservations/check/134', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 134,
          number_of_people: 2,
          registered_clients_count: 0,
          upload_token: 'draft-token'
        })
      });
    });

    await page.goto('/134/remote-checkin/en');

    await page.evaluate(() => {
      const host = document.querySelector('app-remote-checkin');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('RemoteCheckin component instance not available');
      }
      const component = ngRef.getComponent(host);
      localStorage.setItem('checkin-draft:134', JSON.stringify({
        savedAt: Date.now(),
        clientForm: {
          nazionalita: 'ITA',
          stato_nascita: 'ITA',
          cittadinanza: 'ITA'
        }
      }));
      component.clientForm.patchValue({
        nazionalita: '',
        stato_nascita: '',
        cittadinanza: ''
      }, { emitEvent: false });
      (component as any).restoreDraftIfValid();
      if (component.clientForm.get('nazionalita')?.value !== 'ITA') {
        throw new Error('Expected nazionalita to be restored from draft');
      }
      if (component.clientForm.get('stato_nascita')?.value !== 'ITA') {
        throw new Error('Expected stato_nascita to be restored from draft');
      }
      if (component.clientForm.get('cittadinanza')?.value !== 'ITA') {
        throw new Error('Expected cittadinanza to be restored from draft');
      }
    });

    await page.evaluate(() => {
      const host = document.querySelector('app-remote-checkin');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('RemoteCheckin component instance not available');
      }
      const component = ngRef.getComponent(host);
      localStorage.setItem('checkin-draft:134', JSON.stringify({
        savedAt: Date.now() - (6 * 60 * 1000),
        clientForm: {
          nazionalita: 'DEU',
          stato_nascita: 'DEU',
          cittadinanza: 'DEU'
        }
      }));
      (component as any).restoreDraftIfValid();
      component.clientForm.patchValue({
        nazionalita: '',
        stato_nascita: '',
        cittadinanza: ''
      }, { emitEvent: false });
      (component as any).restoreDraftIfValid();
      if (component.clientForm.get('nazionalita')?.value) {
        throw new Error('Expired draft should not restore values');
      }
      if (component.clientForm.get('stato_nascita')?.value) {
        throw new Error('Expired draft should not restore values');
      }
      if (component.clientForm.get('cittadinanza')?.value) {
        throw new Error('Expired draft should not restore values');
      }
      const raw = localStorage.getItem('checkin-draft:134');
      if (raw) {
        throw new Error('Expired draft should be removed from localStorage');
      }
    });
  });

  test('remote check-in prevents duplicate upload submissions', async ({ page }) => {
    let uploadCalls = 0;

    await page.route('**/api/v1/reservations/check/135', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 135,
          number_of_people: 2,
          registered_clients_count: 0,
          upload_token: 'duplicate-submit-token'
        })
      });
    });

    await page.route('**/api/v1/upload', async (route) => {
      uploadCalls += 1;
      await new Promise((resolve) => setTimeout(resolve, 300));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Upload completed' })
      });
    });

    await page.goto('/135/remote-checkin/en');
    await populateRemoteCheckinForms(page);
    await page.evaluate(() => {
      const host = document.querySelector('app-remote-checkin');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('RemoteCheckin component instance not available');
      }
      const component = ngRef.getComponent(host);
      component.reservationId = '135';
      component.canRegister = true;
      component.uploadToken = 'duplicate-submit-token';
      component.uploadReservationData();
      component.uploadReservationData();
    });

    await expect(page).toHaveURL(/\/checkin-complete\/135/);
    expect(uploadCalls).toBe(1);
  });

  test('remote check-in shows registration unavailable when reservation does not exist', async ({ page }) => {
    await page.route('**/api/v1/reservations/check/136', async (route) => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Reservation not found' })
      });
    });

    await page.goto('/136/remote-checkin/en');
    await expect(page.getByText('Registration Unavailable')).toBeVisible();
    await expect(page.locator('#name').first()).toBeDisabled();
    await expect(page.locator('button.p-button:has(.pi-arrow-right)').first()).toBeDisabled();
  });

  test('remote check-in missing upload token message is localized in Italian', async ({ page }) => {
    await page.route('**/api/v1/reservations/check/137', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 137,
          number_of_people: 2,
          registered_clients_count: 0,
          upload_token: null
        })
      });
    });

    await page.goto('/137/remote-checkin/it');
    await populateRemoteCheckinForms(page);
    const expectedLocalizedText = await page.evaluate(() => {
      const host = document.querySelector('app-remote-checkin');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('RemoteCheckin component instance not available');
      }
      const component = ngRef.getComponent(host);
      component.translocoService.setActiveLang('it');
      const expected = component.translocoService.translate('upload-token-missing');
      component.reservationId = '137';
      component.canRegister = true;
      component.uploadToken = null;
      component.uploadReservationData();
      return expected;
    });

    await expect(page.getByText(expectedLocalizedText)).toBeVisible();
  });

  test('remote check-in rejects invalid mime type for each required upload field', async ({ page }) => {
    await page.route('**/api/v1/reservations/check/138', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 138,
          number_of_people: 2,
          registered_clients_count: 0,
          upload_token: 'mime-guard-token'
        })
      });
    });

    await page.goto('/138/remote-checkin/en');
    await populateRemoteCheckinForms(page);
    await page.locator('button.p-button:has(.pi-arrow-right)').first().click();
    await expect(page.locator('app-upload-identity')).toBeVisible();

    await page.evaluate(() => {
      const host = document.querySelector('app-upload-identity');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('UploadIdentity component instance not available');
      }
      const uploadComponent = ngRef.getComponent(host);
      const invalidFile = new File(['bad-content'], 'file.txt', { type: 'text/plain' });
      const fields = ['frontimage', 'backimage', 'selfie'] as const;
      fields.forEach((field) => {
        uploadComponent.onFileSelect({ currentFiles: [invalidFile] }, field);
        if (uploadComponent.uploadForm.get(field)?.value !== null) {
          throw new Error(`Field ${field} should remain empty for invalid MIME`);
        }
      });
      if (uploadComponent.getUploadProgress() !== 0) {
        throw new Error('Invalid mime uploads must not increase upload progress');
      }
    });
  });

  test('remote check-in rejects over-size files for each required upload field', async ({ page }) => {
    await page.route('**/api/v1/reservations/check/139', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 139,
          number_of_people: 2,
          registered_clients_count: 0,
          upload_token: 'size-guard-token'
        })
      });
    });

    await page.goto('/139/remote-checkin/en');
    await populateRemoteCheckinForms(page);
    await page.locator('button.p-button:has(.pi-arrow-right)').first().click();
    await expect(page.locator('app-upload-identity')).toBeVisible();

    await page.evaluate(() => {
      const host = document.querySelector('app-upload-identity');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('UploadIdentity component instance not available');
      }
      const uploadComponent = ngRef.getComponent(host);
      const hugeFile = new File([new Uint8Array(5_000_001)], 'huge.jpg', { type: 'image/jpeg' });
      const fields = ['frontimage', 'backimage', 'selfie'] as const;
      fields.forEach((field) => {
        uploadComponent.onFileSelect({ currentFiles: [hugeFile] }, field);
        if (uploadComponent.uploadForm.get(field)?.value !== null) {
          throw new Error(`Field ${field} should remain empty for over-size file`);
        }
      });
      if (uploadComponent.getUploadProgress() !== 0) {
        throw new Error('Oversize uploads must not increase upload progress');
      }
    });
  });

  test('remote check-in handles upload 502 and re-enables submit state', async ({ page }) => {
    await page.route('**/api/v1/reservations/check/140', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 140,
          number_of_people: 2,
          registered_clients_count: 0,
          upload_token: 'upload-502-token'
        })
      });
    });

    await page.route('**/api/v1/upload', async (route) => {
      await route.fulfill({
        status: 502,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Bad gateway from upstream' })
      });
    });

    await page.goto('/140/remote-checkin/en');
    await populateRemoteCheckinForms(page);
    await page.evaluate(() => {
      const host = document.querySelector('app-remote-checkin');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('RemoteCheckin component instance not available');
      }
      const component = ngRef.getComponent(host);
      component.reservationId = '140';
      component.canRegister = true;
      component.uploadToken = 'upload-502-token';
      component.uploadReservationData();
    });

    await expect(page.getByText('Bad gateway from upstream')).toBeVisible();
    await page.evaluate(() => {
      const host = document.querySelector('app-remote-checkin');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('RemoteCheckin component instance not available');
      }
      const component = ngRef.getComponent(host);
      if (component.isSubmitting) {
        throw new Error('isSubmitting should be false after upload error');
      }
    });
  });

  test('remote check-in handles reservation edge values for capacity fallback', async ({ page }) => {
    await page.route('**/api/v1/reservations/check/141', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 141,
          number_of_people: 2,
          registered_clients_count: 0,
          upload_token: 'edge-capacity-token'
        })
      });
    });

    await page.goto('/141/remote-checkin/en');
    await page.evaluate(() => {
      const host = document.querySelector('app-remote-checkin');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('RemoteCheckin component instance not available');
      }
      const component = ngRef.getComponent(host);

      component.reservationDetails = { number_of_people: 0, registered_clients_count: 0 };
      component.checkRegistrationCapacity();
      if (!component.canRegister) {
        throw new Error('number_of_people=0 should fallback to max=1 and allow first registration');
      }

      component.reservationDetails = { number_of_people: null, registered_clients_count: 0 };
      component.checkRegistrationCapacity();
      if (!component.canRegister) {
        throw new Error('number_of_people=null should fallback to max=1 and allow first registration');
      }

      component.reservationDetails = { number_of_people: 2, registered_clients_count: 'oops' };
      component.checkRegistrationCapacity();
      if (!component.canRegister) {
        throw new Error('Malformed registered_clients_count should not crash and should keep registration available');
      }
    });
  });

  test('remote check-in route handles invalid reservation id safely', async ({ page }) => {
    await page.route('**/api/v1/reservations/check/invalid-id', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Invalid reservation id' })
      });
    });

    await page.goto('/invalid-id/remote-checkin/en');
    await expect(page).toHaveURL(/\/invalid-id\/remote-checkin\/en/);
    await expect(page.getByText('Registration Unavailable')).toBeVisible();
    await expect(page.locator('#name').first()).toBeDisabled();
  });

  test('remote check-in supports keyboard-only step navigation and submit', async ({ page }) => {
    await page.route('**/api/v1/reservations/check/142', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 142,
          number_of_people: 2,
          registered_clients_count: 0,
          upload_token: 'keyboard-flow-token'
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

    await page.goto('/142/remote-checkin/en');
    await populateRemoteCheckinForms(page);
    await page.evaluate(() => {
      const host = document.querySelector('app-remote-checkin');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('RemoteCheckin component instance not available');
      }
      const component = ngRef.getComponent(host);
      component.canRegister = true;
      component.clientForm.enable({ emitEvent: false });
      component.uploadForm.enable({ emitEvent: false });
    });

    const nextBtnStep1 = page.locator('button.p-button:has(.pi-arrow-right)').first();
    await nextBtnStep1.focus();
    await page.keyboard.press('Enter');
    await expect(page.locator('app-upload-identity')).toBeVisible();

    const nextBtnStep2 = page.locator('button.p-button:has(.pi-arrow-right)').first();
    await nextBtnStep2.focus();
    await page.keyboard.press('Enter');

    const submitBtn = page.locator('button.p-button:has(.pi-check)').first();
    await submitBtn.focus();
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(/\/checkin-complete\/142/);
  });

  test('remote check-in keeps focus stable after toast state changes', async ({ page }) => {
    await page.route('**/api/v1/reservations/check/143', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 143,
          number_of_people: 2,
          registered_clients_count: 0,
          upload_token: null
        })
      });
    });

    await page.goto('/143/remote-checkin/en');
    await populateRemoteCheckinForms(page);
    const nextBtn = page.locator('button.p-button:has(.pi-arrow-right)').first();
    await nextBtn.focus();
    await page.evaluate(() => {
      const host = document.querySelector('app-remote-checkin');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('RemoteCheckin component instance not available');
      }
      const component = ngRef.getComponent(host);
      component.reservationId = '143';
      component.canRegister = true;
      component.uploadToken = null;
      component.uploadReservationData();
    });

    await expect(page.getByRole('alert')).toBeVisible();
    await page.evaluate(() => {
      const active = document.activeElement as HTMLElement | null;
      if (!active) {
        throw new Error('Expected an active element after toast state change');
      }
      if (!active.classList.contains('p-button')) {
        throw new Error('Focus should remain on an interactive button after toast');
      }
    });
  });

  test('remote check-in complete flow keeps step-2 next disabled until images are uploaded', async ({ page }) => {
    await page.route('**/api/v1/reservations/check/130', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 130,
          number_of_people: 2,
          registered_clients_count: 0,
          upload_token: 'step2-validation-token'
        })
      });
    });

    await page.goto('/130/remote-checkin/en');
    await populateRemoteCheckinForms(page);
    await page.evaluate(() => {
      const host = document.querySelector('app-remote-checkin');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('RemoteCheckin component instance not available');
      }
      const component = ngRef.getComponent(host);
      component.uploadForm.reset();
      component.canRegister = true;
      component.clientForm.enable({ emitEvent: false });
      component.uploadForm.enable({ emitEvent: false });
      component.uploadForm.updateValueAndValidity();
    });

    await page.locator('button.p-button:has(.pi-arrow-right)').first().click();
    await expect(page.locator('app-upload-identity')).toBeVisible();
    await expect(page.locator('button.p-button:has(.pi-arrow-right)').first()).toBeDisabled();
  });

  test('remote check-in complete flow shows document date validation error', async ({ page }) => {
    await page.route('**/api/v1/reservations/check/131', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 131,
          number_of_people: 2,
          registered_clients_count: 0,
          upload_token: 'date-invalid-token'
        })
      });
    });

    await page.goto('/131/remote-checkin/en');
    await populateRemoteCheckinForms(page);
    await page.evaluate(() => {
      const host = document.querySelector('app-remote-checkin');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('RemoteCheckin component instance not available');
      }
      const component = ngRef.getComponent(host);
      component.reservationId = '131';
      component.canRegister = true;
      component.uploadToken = 'date-invalid-token';
      component.clientForm.patchValue({
        data_emissione: new Date('2028-02-13T10:00:00.000Z'),
        data_scadenza: new Date('2028-02-13T10:00:00.000Z')
      });
      component.uploadReservationData();
    });

    await expect(page.getByRole('alert').getByText('Document expiry date must be after the issue date')).toBeVisible();
  });

  test('remote check-in complete flow shows fallback upload error when backend has no detail', async ({ page }) => {
    await page.route('**/api/v1/reservations/check/132', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 132,
          number_of_people: 2,
          registered_clients_count: 0,
          upload_token: 'upload-fallback-error-token'
        })
      });
    });

    await page.route('**/api/v1/upload', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({})
      });
    });

    await page.goto('/132/remote-checkin/en');
    await populateRemoteCheckinForms(page);
    await page.evaluate(() => {
      const host = document.querySelector('app-remote-checkin');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('RemoteCheckin component instance not available');
      }
      const component = ngRef.getComponent(host);
      component.reservationId = '132';
      component.canRegister = true;
      component.uploadToken = 'upload-fallback-error-token';
      component.uploadReservationData();
    });

    await expect(page.getByText('Upload failed')).toBeVisible();
  });

  test('remote check-in complete flow blocks submit when registration becomes unavailable', async ({ page }) => {
    await page.route('**/api/v1/reservations/check/133', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 133,
          number_of_people: 2,
          registered_clients_count: 0,
          upload_token: 'registration-closed-token'
        })
      });
    });

    await page.goto('/133/remote-checkin/en');
    await populateRemoteCheckinForms(page);
    await page.evaluate(() => {
      const host = document.querySelector('app-remote-checkin');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('RemoteCheckin component instance not available');
      }
      const component = ngRef.getComponent(host);
      component.reservationId = '133';
      component.canRegister = false;
      component.uploadToken = 'registration-closed-token';
      component.uploadReservationData();
    });

    await expect(page.getByRole('alert').getByText('This reservation is full and no longer accepting new registrations')).toBeVisible();
  });

  test('remote check-in complete flow fills data and uploads images', async ({ page }) => {
    let uploadCalled = false;
    let uploadTokenHeader = '';

    await page.route('**/api/v1/reservations/check/125', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 125,
          number_of_people: 2,
          registered_clients_count: 0,
          upload_token: 'complete-flow-token'
        })
      });
    });

    await page.route('**/api/v1/upload', async (route) => {
      uploadCalled = true;
      uploadTokenHeader = route.request().headers()['x-upload-token'] || '';
      const postData = route.request().postDataBuffer();
      expect(postData).toBeTruthy();
      if (postData) {
        const payload = postData.toString('utf8');
        expect(payload).toContain('name="frontimage"');
        expect(payload).toContain('name="backimage"');
        expect(payload).toContain('name="selfie"');
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Upload completed' })
      });
    });

    await page.goto('/125/remote-checkin/en');
    await populateRemoteCheckinForms(page);
    await page.evaluate(() => {
      const host = document.querySelector('app-remote-checkin');
      const ngRef = (window as any).ng;
      if (!host || !ngRef?.getComponent) {
        throw new Error('RemoteCheckin component instance not available');
      }
      const component = ngRef.getComponent(host);
      component.canRegister = true;
      component.clientForm.enable({ emitEvent: false });
      component.uploadForm.enable({ emitEvent: false });
    });

    await page.locator('button.p-button:has(.pi-arrow-right)').first().click();
    await expect(page.locator('app-upload-identity')).toBeVisible();

    await page.locator('button.p-button:has(.pi-arrow-right)').first().click();
    await page.locator('button.p-button:has(.pi-check)').first().click();

    await expect(page).toHaveURL(/\/checkin-complete\/125/);
    expect(uploadCalled).toBe(true);
    expect(uploadTokenHeader).toBe('complete-flow-token');
  });

  test('landing header language switch updates translated labels', async ({ page }) => {
    await page.goto('/landing');
    await expect(page.locator('.header__signin')).toHaveText('Sign in');

    await page.hover('.language-menu');
    await page.click('.language-menu__list button:has-text("Italiano")');

    await expect(page.locator('.header__signin')).toHaveText('Accedi');
  });
});
