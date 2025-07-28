import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ReservationService } from './reservation.service';
import { AuthService } from './auth.service';
import { environment } from '../../environments/environments';
import { HttpHeaders } from '@angular/common/http';

describe('ReservationService', () => {
  let service: ReservationService;
  let httpMock: HttpTestingController;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  const baseUrl = `${environment.apiBaseUrl}/api/v1/reservations`;
  const mockAuthHeaders = new HttpHeaders({
    'Authorization': 'Bearer mock-token',
    'Content-Type': 'application/json'
  });

  beforeEach(() => {
    const spy = jasmine.createSpyObj('AuthService', ['getAuthHeaders']);

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        ReservationService,
        { provide: AuthService, useValue: spy }
      ]
    });

    service = TestBed.inject(ReservationService);
    httpMock = TestBed.inject(HttpTestingController);
    authServiceSpy = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    authServiceSpy.getAuthHeaders.and.returnValue(mockAuthHeaders);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('createReservation', () => {
    it('should create a reservation with valid data', () => {
      const mockReservation = {
        id: 1,
        structureId: 123,
        userId: 456,
        startDate: '2024-01-15',
        endDate: '2024-01-20',
        status: 'pending'
      };
      const mockResponse = { ...mockReservation, id: 1, createdAt: '2024-01-01' };

      service.createReservation(mockReservation).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(baseUrl);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(mockReservation);
      expect(req.request.headers).toEqual(mockAuthHeaders);
      req.flush(mockResponse);
    });

    it('should handle empty reservation object', () => {
      const emptyReservation = {};
      const mockResponse = { error: 'Invalid reservation data' };

      service.createReservation(emptyReservation).subscribe(
        response => fail('Should have failed'),
        error => expect(error.error).toEqual(mockResponse)
      );

      const req = httpMock.expectOne(baseUrl);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(emptyReservation);
      req.flush(mockResponse, { status: 400, statusText: 'Bad Request' });
    });

    it('should handle null reservation data', () => {
      const nullReservation = null;

      service.createReservation(nullReservation).subscribe(response => {
        expect(response).toBeDefined();
      });

      const req = httpMock.expectOne(baseUrl);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toBeNull();
      req.flush({ id: 1 });
    });

    it('should include auth headers in request', () => {
      const mockReservation = { structureId: 123 };

      service.createReservation(mockReservation).subscribe();

      const req = httpMock.expectOne(baseUrl);
      expect(authServiceSpy.getAuthHeaders).toHaveBeenCalled();
      expect(req.request.headers).toEqual(mockAuthHeaders);
      req.flush({});
    });

    it('should handle server errors', () => {
      const mockReservation = { structureId: 123 };

      service.createReservation(mockReservation).subscribe(
        response => fail('Should have failed'),
        error => expect(error.status).toBe(500)
      );

      const req = httpMock.expectOne(baseUrl);
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });
    });
  });

  describe('updateReservation', () => {
    it('should update a reservation with valid data', () => {
      const reservationId = 123;
      const mockReservation = {
        structureId: 456,
        startDate: '2024-02-01',
        endDate: '2024-02-05',
        status: 'confirmed'
      };
      const mockResponse = { ...mockReservation, id: reservationId, updatedAt: '2024-01-15' };

      service.updateReservation(mockReservation, reservationId).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      const expectedUrl = `${baseUrl}/${reservationId}`;
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('PATCH');
      expect(req.request.body).toEqual(mockReservation);
      expect(req.request.headers).toEqual(mockAuthHeaders);
      req.flush(mockResponse);
    });

    it('should handle zero reservation ID', () => {
      const reservationId = 0;
      const mockReservation = { status: 'cancelled' };

      service.updateReservation(mockReservation, reservationId).subscribe();

      const expectedUrl = `${baseUrl}/0`;
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('PATCH');
      req.flush({});
    });

    it('should handle negative reservation ID', () => {
      const reservationId = -1;
      const mockReservation = { status: 'cancelled' };

      service.updateReservation(mockReservation, reservationId).subscribe();

      const expectedUrl = `${baseUrl}/-1`;
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('PATCH');
      req.flush({});
    });

    it('should handle large reservation ID', () => {
      const reservationId = 999999999;
      const mockReservation = { status: 'confirmed' };

      service.updateReservation(mockReservation, reservationId).subscribe();

      const expectedUrl = `${baseUrl}/${reservationId}`;
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('PATCH');
      req.flush({});
    });

    it('should handle 404 error for non-existent reservation', () => {
      const reservationId = 999;
      const mockReservation = { status: 'confirmed' };

      service.updateReservation(mockReservation, reservationId).subscribe(
        response => fail('Should have failed'),
        error => expect(error.status).toBe(404)
      );

      const expectedUrl = `${baseUrl}/${reservationId}`;
      const req = httpMock.expectOne(expectedUrl);
      req.flush('Not Found', { status: 404, statusText: 'Not Found' });
    });
  });

  describe('getReservationByStructureId', () => {
    it('should get reservations by structure ID', () => {
      const structureId = 123;
      const mockReservations = [
        { id: 1, structureId: 123, status: 'confirmed' },
        { id: 2, structureId: 123, status: 'pending' }
      ];

      service.getReservationByStructureId(structureId).subscribe(reservations => {
        expect(reservations).toEqual(mockReservations);
        expect(reservations.length).toBe(2);
      });

      const expectedUrl = `${baseUrl}/structure/${structureId}`;
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('GET');
      expect(req.request.headers).toEqual(mockAuthHeaders);
      req.flush(mockReservations);
    });

    it('should handle zero structure ID', () => {
      const structureId = 0;

      service.getReservationByStructureId(structureId).subscribe();

      const expectedUrl = `${baseUrl}/structure/0`;
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should handle negative structure ID', () => {
      const structureId = -1;

      service.getReservationByStructureId(structureId).subscribe();

      const expectedUrl = `${baseUrl}/structure/-1`;
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should return empty array for structure with no reservations', () => {
      const structureId = 456;

      service.getReservationByStructureId(structureId).subscribe(reservations => {
        expect(reservations).toEqual([]);
        expect(reservations.length).toBe(0);
      });

      const expectedUrl = `${baseUrl}/structure/${structureId}`;
      const req = httpMock.expectOne(expectedUrl);
      req.flush([]);
    });

    it('should handle server error gracefully', () => {
      const structureId = 123;

      service.getReservationByStructureId(structureId).subscribe(
        response => fail('Should have failed'),
        error => expect(error.status).toBe(500)
      );

      const expectedUrl = `${baseUrl}/structure/${structureId}`;
      const req = httpMock.expectOne(expectedUrl);
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });
    });
  });

  describe('getMonthlyReservation', () => {
    it('should get monthly reservations for structure', () => {
      const structureId = 123;
      const mockMonthlyData = {
        month: '2024-01',
        reservations: [
          { id: 1, date: '2024-01-15' },
          { id: 2, date: '2024-01-20' }
        ],
        totalReservations: 2,
        revenue: 1500
      };

      service.getMonthlyReservation(structureId).subscribe(data => {
        expect(data).toEqual(mockMonthlyData);
        expect(data.totalReservations).toBe(2);
      });

      const expectedUrl = `${baseUrl}/monthly/${structureId}`;
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('GET');
      expect(req.request.headers).toEqual(mockAuthHeaders);
      req.flush(mockMonthlyData);
    });

    it('should handle zero structure ID for monthly data', () => {
      const structureId = 0;

      service.getMonthlyReservation(structureId).subscribe();

      const expectedUrl = `${baseUrl}/monthly/0`;
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('GET');
      req.flush({ reservations: [], totalReservations: 0 });
    });

    it('should handle unauthorized access', () => {
      const structureId = 123;

      service.getMonthlyReservation(structureId).subscribe(
        response => fail('Should have failed'),
        error => expect(error.status).toBe(401)
      );

      const expectedUrl = `${baseUrl}/monthly/${structureId}`;
      const req = httpMock.expectOne(expectedUrl);
      req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });
    });
  });

  describe('getReservationById', () => {
    it('should get reservation by ID', () => {
      const reservationId = 123;
      const mockReservation = {
        id: 123,
        structureId: 456,
        userId: 789,
        startDate: '2024-01-15',
        endDate: '2024-01-20',
        status: 'confirmed'
      };

      service.getReservationById(reservationId).subscribe(reservation => {
        expect(reservation).toEqual(mockReservation);
        expect(reservation.id).toBe(reservationId);
      });

      const expectedUrl = `${baseUrl}/${reservationId}`;
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('GET');
      expect(req.request.headers).toEqual(mockAuthHeaders);
      req.flush(mockReservation);
    });

    it('should handle zero reservation ID', () => {
      const reservationId = 0;

      service.getReservationById(reservationId).subscribe();

      const expectedUrl = `${baseUrl}/0`;
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('GET');
      req.flush(null);
    });

    it('should handle non-existent reservation ID', () => {
      const reservationId = 999;

      service.getReservationById(reservationId).subscribe(
        response => fail('Should have failed'),
        error => expect(error.status).toBe(404)
      );

      const expectedUrl = `${baseUrl}/${reservationId}`;
      const req = httpMock.expectOne(expectedUrl);
      req.flush('Not Found', { status: 404, statusText: 'Not Found' });
    });

    it('should handle network error', () => {
      const reservationId = 123;

      service.getReservationById(reservationId).subscribe(
        response => fail('Should have failed'),
        error => expect(error.name).toBe('HttpErrorResponse')
      );

      const expectedUrl = `${baseUrl}/${reservationId}`;
      const req = httpMock.expectOne(expectedUrl);
      req.error(new ErrorEvent('Network error'));
    });
  });

  describe('updateReservationStatus', () => {
    it('should update reservation status', () => {
      const reservationId = 123;
      const newStatus = 'confirmed';
      const mockResponse = { id: reservationId, status: newStatus, updatedAt: '2024-01-15' };

      service.updateReservationStatus(reservationId, newStatus).subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(response.status).toBe(newStatus);
      });

      const expectedUrl = `${baseUrl}/${reservationId}/status`;
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('PUT');
      expect(req.request.body).toEqual({ status: newStatus });
      expect(req.request.headers).toEqual(mockAuthHeaders);
      req.flush(mockResponse);
    });

    it('should handle various status values', () => {
      const reservationId = 123;
      const statusValues = ['pending', 'confirmed', 'cancelled', 'completed'];

      statusValues.forEach(status => {
        service.updateReservationStatus(reservationId, status).subscribe();

        const expectedUrl = `${baseUrl}/${reservationId}/status`;
        const req = httpMock.expectOne(expectedUrl);
        expect(req.request.method).toBe('PUT');
        expect(req.request.body).toEqual({ status });
        req.flush({ status });
      });
    });

    it('should handle null status', () => {
      const reservationId = 123;
      const nullStatus = null;

      service.updateReservationStatus(reservationId, nullStatus).subscribe();

      const expectedUrl = `${baseUrl}/${reservationId}/status`;
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.body).toEqual({ status: null });
      req.flush({});
    });

    it('should handle empty string status', () => {
      const reservationId = 123;
      const emptyStatus = '';

      service.updateReservationStatus(reservationId, emptyStatus).subscribe();

      const expectedUrl = `${baseUrl}/${reservationId}/status`;
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.body).toEqual({ status: '' });
      req.flush({});
    });

    it('should handle object status', () => {
      const reservationId = 123;
      const objectStatus = { value: 'confirmed', reason: 'Payment received' };

      service.updateReservationStatus(reservationId, objectStatus).subscribe();

      const expectedUrl = `${baseUrl}/${reservationId}/status`;
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.body).toEqual({ status: objectStatus });
      req.flush({});
    });

    it('should handle forbidden status update', () => {
      const reservationId = 123;
      const status = 'confirmed';

      service.updateReservationStatus(reservationId, status).subscribe(
        response => fail('Should have failed'),
        error => expect(error.status).toBe(403)
      );

      const expectedUrl = `${baseUrl}/${reservationId}/status`;
      const req = httpMock.expectOne(expectedUrl);
      req.flush('Forbidden', { status: 403, statusText: 'Forbidden' });
    });
  });

  describe('deleteReservation', () => {
    it('should delete reservation successfully', () => {
      const reservationId = 123;
      const mockResponse = { message: 'Reservation deleted successfully' };

      service.deleteReservation(reservationId).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      const expectedUrl = `${baseUrl}/${reservationId}`;
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('DELETE');
      expect(req.request.headers).toEqual(mockAuthHeaders);
      req.flush(mockResponse);
    });

    it('should handle zero reservation ID for deletion', () => {
      const reservationId = 0;

      service.deleteReservation(reservationId).subscribe();

      const expectedUrl = `${baseUrl}/0`;
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('DELETE');
      req.flush({});
    });

    it('should handle negative reservation ID for deletion', () => {
      const reservationId = -1;

      service.deleteReservation(reservationId).subscribe();

      const expectedUrl = `${baseUrl}/-1`;
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('DELETE');
      req.flush({});
    });

    it('should handle non-existent reservation deletion', () => {
      const reservationId = 999;

      service.deleteReservation(reservationId).subscribe(
        response => fail('Should have failed'),
        error => expect(error.status).toBe(404)
      );

      const expectedUrl = `${baseUrl}/${reservationId}`;
      const req = httpMock.expectOne(expectedUrl);
      req.flush('Not Found', { status: 404, statusText: 'Not Found' });
    });

    it('should handle unauthorized deletion attempt', () => {
      const reservationId = 123;

      service.deleteReservation(reservationId).subscribe(
        response => fail('Should have failed'),
        error => expect(error.status).toBe(401)
      );

      const expectedUrl = `${baseUrl}/${reservationId}`;
      const req = httpMock.expectOne(expectedUrl);
      req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });
    });

    it('should handle server error during deletion', () => {
      const reservationId = 123;

      service.deleteReservation(reservationId).subscribe(
        response => fail('Should have failed'),
        error => expect(error.status).toBe(500)
      );

      const expectedUrl = `${baseUrl}/${reservationId}`;
      const req = httpMock.expectOne(expectedUrl);
      req.flush('Internal Server Error', { status: 500, statusText: 'Internal Server Error' });
    });
  });

  describe('Service Configuration', () => {
    it('should have correct API URL configuration', () => {
      expect(service['apiUrl']).toBe(`${environment.apiBaseUrl}/api/v1/reservations`);
    });

    it('should be injectable as root service', () => {
      const injectedService = TestBed.inject(ReservationService);
      expect(injectedService).toBe(service);
    });

    it('should properly inject dependencies', () => {
      expect(service['http']).toBeDefined();
      expect(service['authService']).toBeDefined();
    });
  });

  describe('Auth Headers Integration', () => {
    it('should call getAuthHeaders for all HTTP requests', () => {
      const mockReservation = { id: 1 };
      const reservationId = 123;

      // Test all methods that should call getAuthHeaders
      service.createReservation(mockReservation).subscribe();
      service.updateReservation(mockReservation, reservationId).subscribe();
      service.getReservationByStructureId(reservationId).subscribe();
      service.getMonthlyReservation(reservationId).subscribe();
      service.getReservationById(reservationId).subscribe();
      service.updateReservationStatus(reservationId, 'confirmed').subscribe();
      service.deleteReservation(reservationId).subscribe();

      // Verify all requests
      const requests = httpMock.match(() => true);
      expect(requests.length).toBe(7);
      expect(authServiceSpy.getAuthHeaders).toHaveBeenCalledTimes(7);

      requests.forEach(req => {
        expect(req.request.headers).toEqual(mockAuthHeaders);
        req.flush({});
      });
    });

    it('should handle auth service returning null headers', () => {
      authServiceSpy.getAuthHeaders.and.returnValue(null as any);
      const mockReservation = { id: 1 };

      service.createReservation(mockReservation).subscribe();

      const req = httpMock.expectOne(baseUrl);
      expect(req.request.headers.get('Authorization')).toBeNull();
      req.flush({});
    });

    it('should handle auth service returning undefined headers', () => {
      authServiceSpy.getAuthHeaders.and.returnValue(undefined as any);
      const mockReservation = { id: 1 };

      service.createReservation(mockReservation).subscribe();

      const req = httpMock.expectOne(baseUrl);
      expect(req.request.headers.get('Authorization')).toBeNull();
      req.flush({});
    });
  });

  describe('Error Handling', () => {
    it('should handle HTTP client errors gracefully', () => {
      const mockReservation = { id: 1 };
      const errorMessage = 'Http failure response';

      service.createReservation(mockReservation).subscribe(
        response => fail('Should have failed'),
        error => {
          expect(error.message).toContain(errorMessage);
        }
      );

      const req = httpMock.expectOne(baseUrl);
      req.error(new ErrorEvent('Network error'), { status: 0, statusText: errorMessage });
    });

    it('should handle timeout errors', () => {
      const mockReservation = { id: 1 };

      service.createReservation(mockReservation).subscribe(
        response => fail('Should have failed'),
        error => {
          expect(error.status).toBe(408);
        }
      );

      const req = httpMock.expectOne(baseUrl);
      req.flush('Request Timeout', { status: 408, statusText: 'Request Timeout' });
    });

    it('should handle malformed response data', () => {
      const mockReservation = { id: 1 };
      const malformedResponse = 'This is not JSON';

      service.createReservation(mockReservation).subscribe(response => {
        expect(response).toBe(malformedResponse);
      });

      const req = httpMock.expectOne(baseUrl);
      req.flush(malformedResponse);
    });
  });
});
