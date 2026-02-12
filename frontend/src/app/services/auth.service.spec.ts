import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { AuthService } from './auth.service';

function buildToken(expSeconds: number): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = btoa(JSON.stringify({ exp: expSeconds }));
  return `${header}.${payload}.signature`;
}

describe('AuthService', () => {
  let service: AuthService;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideRouter([])]
    });
    service = TestBed.inject(AuthService);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should return false when token is missing', () => {
    localStorage.removeItem('admin_token');
    expect(service.isTokenValid()).toBeFalse();
  });

  it('should return false when token is expired', () => {
    localStorage.setItem('admin_token', buildToken(Math.floor(Date.now() / 1000) - 5));
    expect(service.isTokenValid()).toBeFalse();
  });

  it('should report logged-in when user exists and token is valid', () => {
    localStorage.setItem('user', JSON.stringify({ id: 1, role: 'administrator' }));
    localStorage.setItem('admin_token', buildToken(Math.floor(Date.now() / 1000) + 600));
    expect(service.isLoggedIn()).toBeTrue();
  });

  it('should return false for malformed token payload', () => {
    localStorage.setItem('admin_token', 'not.a.jwt');
    expect(service.isTokenValid()).toBeFalse();
  });

  it('should return empty auth headers when token is missing', () => {
    localStorage.removeItem('admin_token');
    expect(service.getAuthHeaders().keys().length).toBe(0);
  });
});
