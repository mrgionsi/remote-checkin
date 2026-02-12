import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, UrlTree } from '@angular/router';

import { AuthService } from '../services/auth.service';
import { superadminGuard } from './superadmin.guard';

describe('superadminGuard', () => {
  let router: Router;
  const authServiceStub = {
    isLoggedIn: () => false,
    isSuperAdmin: () => false
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: authServiceStub }
      ]
    });
    router = TestBed.inject(Router);
  });

  it('should redirect to /admin/login when user is not logged in', () => {
    spyOn(authServiceStub, 'isLoggedIn').and.returnValue(false);
    const result = TestBed.runInInjectionContext(() =>
      superadminGuard({} as any, { url: '/admin/superadmin' } as any)
    );
    expect(result instanceof UrlTree).toBeTrue();
    expect(router.serializeUrl(result as UrlTree)).toBe('/admin/login');
  });

  it('should redirect to /admin/dashboard when not superadmin', () => {
    spyOn(authServiceStub, 'isLoggedIn').and.returnValue(true);
    spyOn(authServiceStub, 'isSuperAdmin').and.returnValue(false);
    const result = TestBed.runInInjectionContext(() =>
      superadminGuard({} as any, { url: '/admin/superadmin' } as any)
    );
    expect(result instanceof UrlTree).toBeTrue();
    expect(router.serializeUrl(result as UrlTree)).toBe('/admin/dashboard');
  });

  it('should allow access for superadmin', () => {
    spyOn(authServiceStub, 'isLoggedIn').and.returnValue(true);
    spyOn(authServiceStub, 'isSuperAdmin').and.returnValue(true);
    const result = TestBed.runInInjectionContext(() =>
      superadminGuard({} as any, { url: '/admin/superadmin' } as any)
    );
    expect(result).toBeTrue();
  });
});
