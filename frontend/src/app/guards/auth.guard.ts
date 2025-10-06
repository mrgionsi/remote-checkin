import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    // Check if we're in a browser environment first
    if (typeof window === 'undefined') {
        console.log('authGuard: Running on server side, allowing access');
        return true; // Allow access during SSR, let client-side handle auth
    }

    // Check if localStorage is available
    if (!window.localStorage) {
        console.log('authGuard: localStorage not available, allowing access');
        return true; // Allow access if localStorage not ready, let component handle it
    }

    // Check if user is logged in
    const isLoggedIn = authService.isLoggedIn();
    console.log('authGuard: isLoggedIn =', isLoggedIn, 'for route:', state.url);

    if (!isLoggedIn) {
        console.log('authGuard: Redirecting to login from', state.url);
        router.navigate(['/admin/login']);
        return false;
    }

    console.log('authGuard: Allowing access to', state.url);
    return true;
};