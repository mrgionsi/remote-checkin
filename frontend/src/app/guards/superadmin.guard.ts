import { inject } from '@angular/core';
import { CanActivateFn, Router, UrlTree } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const superadminGuard: CanActivateFn = (route, state): boolean | UrlTree => {
    const authService = inject(AuthService);
    const router = inject(Router);

    // Check if we're in a browser environment first
    // During SSR, deny access to protected routes - they'll be handled on client-side
    if (typeof window === 'undefined') {
        console.log('superadminGuard: Running on server side, denying access (client will handle auth)');
        return false; // Deny access during SSR, client-side will re-evaluate
    }

    // Check if localStorage is available - treat as unauthenticated
    if (!window.localStorage) {
        console.log('superadminGuard: localStorage not available, redirecting to login');
        return router.parseUrl('/admin/login');
    }

    // Check if user is logged in
    const isLoggedIn = authService.isLoggedIn();
    console.log('superadminGuard: isLoggedIn =', isLoggedIn, 'for route:', state.url);

    if (!isLoggedIn) {
        console.log('superadminGuard: Not logged in, redirecting to login from', state.url);
        return router.parseUrl('/admin/login');
    }

    // Check if user is superadmin
    const isSuperAdmin = authService.isSuperAdmin();
    console.log('superadminGuard: isSuperAdmin =', isSuperAdmin, 'for route:', state.url);

    if (!isSuperAdmin) {
        console.log('superadminGuard: Not superadmin, redirecting to dashboard from', state.url);
        return router.parseUrl('/admin/dashboard');
    }

    console.log('superadminGuard: Allowing access to', state.url);
    return true;
};
