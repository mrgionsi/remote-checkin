import { HttpHeaders } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { environment } from '../../environments/environments';
import { AuthService } from './auth.service';
import { SuperadminService } from './superadmin.service';

describe('SuperadminService', () => {
  let service: SuperadminService;
  let httpMock: HttpTestingController;

  const authHeaders = new HttpHeaders({ Authorization: 'Bearer test-token' });
  const authServiceStub = {
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

    service = TestBed.inject(SuperadminService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should build structures URL with filters', () => {
    service.getStructures({ page: 2, per_page: 20, search: 'rome', is_active: 'true' }).subscribe();

    const req = httpMock.expectOne(
      `${environment.apiBaseUrl}/api/v1/superadmin/structures?page=2&per_page=20&search=rome&is_active=true`
    );
    expect(req.request.method).toBe('GET');
    expect(req.request.headers.get('Authorization')).toBe('Bearer test-token');
    req.flush({ structures: [] });
  });

  it('should send delete association payload in request body', () => {
    service.deleteAssociation(11, 22).subscribe();

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/superadmin/associations`);
    expect(req.request.method).toBe('DELETE');
    expect(req.request.body).toEqual({ user_id: 11, structure_id: 22 });
    req.flush({ message: 'ok' });
  });

  it('should call change-role endpoint with id_role payload', () => {
    service.changeUserRole(5, 2).subscribe();

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/superadmin/users/5/change-role`);
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual({ id_role: 2 });
    req.flush({ message: 'ok' });
  });
});
