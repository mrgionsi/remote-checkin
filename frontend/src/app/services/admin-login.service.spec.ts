import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { AdminLoginService } from './admin-login.service';
import { environment } from '../../environments/environments';

describe('AdminLoginService', () => {
  let service: AdminLoginService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()]
    });
    service = TestBed.inject(AdminLoginService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should post login payload', () => {
    service.login('admin', 'password').subscribe((response) => {
      expect(response.access_token).toBe('token');
      expect(response.user.username).toBe('admin');
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/admin/login`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ username: 'admin', password: 'password' });
    req.flush({
      access_token: 'token',
      user: {
        id: 1,
        username: 'admin',
        name: 'Admin',
        surname: 'User',
        structures: [],
        role: 'administrator'
      }
    });
  });
});
