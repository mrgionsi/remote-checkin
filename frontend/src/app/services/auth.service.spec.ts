import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { provideRouter } from '@angular/router';
import { AuthService } from './auth.service';

function buildToken(expSeconds: number): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = btoa(JSON.stringify({ exp: expSeconds }));
  return `${header}.${payload}.signature`;
}

describe('AuthService', () => {
  let service: AuthService;
  let router: Router;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideRouter([])]
    });
    service = TestBed.inject(AuthService);
    router = TestBed.inject(Router);
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

  it('should return authorization header when token exists', () => {
    localStorage.setItem('admin_token', buildToken(Math.floor(Date.now() / 1000) + 600));
    expect(service.getAuthHeaders().get('Authorization')).toContain('Bearer ');
  });

  it('should redirect to login and return false when auth check fails', async () => {
    const navigateSpy = spyOn(router, 'navigate').and.resolveTo(true);
    localStorage.removeItem('user');
    localStorage.removeItem('admin_token');

    expect(service.checkAuthAndRedirect()).toBeFalse();
    expect(navigateSpy).toHaveBeenCalledWith(['/admin/login']);
  });

  it('should return true without redirect when auth check passes', () => {
    const navigateSpy = spyOn(router, 'navigate');
    localStorage.setItem('user', JSON.stringify({ id: 1, role: 'superadmin' }));
    localStorage.setItem('admin_token', buildToken(Math.floor(Date.now() / 1000) + 600));

    expect(service.checkAuthAndRedirect()).toBeTrue();
    expect(service.isSuperAdmin()).toBeTrue();
    expect(navigateSpy).not.toHaveBeenCalled();
  });
});
