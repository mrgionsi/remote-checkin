import { HttpHeaders, provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { environment } from '../../environments/environments';
import { AuthService } from './auth.service';
import { ReservationService } from './reservation.service';

describe('ReservationService', () => {
  let service: ReservationService;
  let httpMock: HttpTestingController;
  let checkAuthAndRedirectSpy: jasmine.Spy;

  const authHeaders = new HttpHeaders({ Authorization: 'Bearer test-token' });
  const authServiceStub = {
    checkAuthAndRedirect: () => true,
    getAuthHeaders: () => authHeaders
  };

  beforeEach(() => {
    checkAuthAndRedirectSpy = spyOn(authServiceStub, 'checkAuthAndRedirect').and.returnValue(true);

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: AuthService, useValue: authServiceStub }
      ]
    });

    service = TestBed.inject(ReservationService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create a reservation when authenticated', () => {
    const payload = { roomName: 'A1' };

    service.createReservation(payload).subscribe((res) => {
      expect(res).toEqual({ id: 1 });
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/reservations`);
    expect(req.request.method).toBe('POST');
    expect(req.request.headers.get('Authorization')).toBe('Bearer test-token');
    expect(req.request.body).toEqual(payload);
    req.flush({ id: 1 });
  });

  it('should not call API when auth check fails', () => {
    checkAuthAndRedirectSpy.and.returnValue(false);

    service.createReservation({}).subscribe({
      next: () => fail('Expected auth failure'),
      error: (error) => expect(String(error.message)).toContain('Authentication failed')
    });

    httpMock.expectNone(`${environment.apiBaseUrl}/api/v1/reservations`);
  });

  it('should fetch monthly reservations with auth header', () => {
    service.getMonthlyReservation(3).subscribe((res) => {
      expect(res).toEqual([{ month: 'Jan', total_reservations: 5 }]);
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/reservations/monthly/3`);
    expect(req.request.method).toBe('GET');
    expect(req.request.headers.get('Authorization')).toBe('Bearer test-token');
    req.flush([{ month: 'Jan', total_reservations: 5 }]);
  });
});
