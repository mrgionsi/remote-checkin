import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, UrlTree } from '@angular/router';

import { AuthService } from '../services/auth.service';
import { authGuard } from './auth.guard';

describe('authGuard', () => {
  let router: Router;
  const authServiceStub = {
    isLoggedIn: () => false
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

  it('should redirect to /admin/login when not logged in', () => {
    spyOn(authServiceStub, 'isLoggedIn').and.returnValue(false);
    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as any, { url: '/admin/dashboard' } as any)
    );
    expect(result instanceof UrlTree).toBeTrue();
    expect(router.serializeUrl(result as UrlTree)).toBe('/admin/login');
  });

  it('should allow access when logged in', () => {
    spyOn(authServiceStub, 'isLoggedIn').and.returnValue(true);
    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as any, { url: '/admin/dashboard' } as any)
    );
    expect(result).toBeTrue();
  });
});
