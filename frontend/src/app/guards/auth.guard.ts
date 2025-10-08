import { inject } from '@angular/core';
import { CanActivateFn, Router, UrlTree } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state): boolean | UrlTree => {
    const authService = inject(AuthService);
    const router = inject(Router);

    // Check if we're in a browser environment first
    // During SSR, deny access to protected routes - they'll be handled on client-side
    if (typeof window === 'undefined') {
        console.log('authGuard: Running on server side, denying access (client will handle auth)');
        return false; // Deny access during SSR, client-side will re-evaluate
    }

    // Check if localStorage is available - treat as unauthenticated
    if (!window.localStorage) {
        console.log('authGuard: localStorage not available, redirecting to login');
        return router.parseUrl('/admin/login');
    }

    // Check if user is logged in
    const isLoggedIn = authService.isLoggedIn();
    console.log('authGuard: isLoggedIn =', isLoggedIn, 'for route:', state.url);

    if (!isLoggedIn) {
        console.log('authGuard: Not logged in, redirecting to login from', state.url);
        return router.parseUrl('/admin/login');
    }

    console.log('authGuard: Allowing access to', state.url);
    return true;
};