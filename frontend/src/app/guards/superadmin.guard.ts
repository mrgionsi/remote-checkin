import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const superadminGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    // Check if we're in a browser environment first
    if (typeof window === 'undefined') {
        console.log('superadminGuard: Running on server side, allowing access');
        return true; // Allow access during SSR, let client-side handle auth
    }

    // Check if localStorage is available
    if (!window.localStorage) {
        console.log('superadminGuard: localStorage not available, allowing access');
        return true; // Allow access if localStorage not ready, let component handle it
    }

    // Check if user is logged in
    const isLoggedIn = authService.isLoggedIn();
    console.log('superadminGuard: isLoggedIn =', isLoggedIn, 'for route:', state.url);

    if (!isLoggedIn) {
        console.log('superadminGuard: Redirecting to login from', state.url);
        router.navigate(['/admin/login']);
        return false;
    }

    // Check if user is superadmin
    const isSuperAdmin = authService.isSuperAdmin();
    console.log('superadminGuard: isSuperAdmin =', isSuperAdmin, 'for route:', state.url);

    if (!isSuperAdmin) {
        console.log('superadminGuard: Redirecting to admin dashboard from', state.url);
        // Redirect to admin dashboard if not superadmin
        router.navigate(['/admin/dashboard']);
        return false;
    }

    console.log('superadminGuard: Allowing access to', state.url);
    return true;
};
