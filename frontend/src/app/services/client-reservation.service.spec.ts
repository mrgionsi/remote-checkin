import { TestBed } from '@angular/core/testing';
import { HttpHeaders, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { ClientReservationService } from './client-reservation.service';
import { AuthService } from './auth.service';
import { environment } from '../../environments/environments';

describe('ClientReservationService', () => {
  let service: ClientReservationService;
  let httpMock: HttpTestingController;

  const authHeaders = new HttpHeaders({ Authorization: 'Bearer test-token' });
  const authServiceStub = {
    checkAuthAndRedirect: () => true,
    getAuthHeaders: () => authHeaders
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: AuthService, useValue: authServiceStub }
      ]
    });
    service = TestBed.inject(ClientReservationService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get clients by reservation id with auth headers', () => {
    service.getClientByReservationId(7).subscribe((res) => {
      expect(res).toEqual([{ id: 1 }]);
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/reservations/7/clients`);
    expect(req.request.method).toBe('GET');
    expect(req.request.headers.get('Authorization')).toBe('Bearer test-token');
    req.flush([{ id: 1 }]);
  });
});
