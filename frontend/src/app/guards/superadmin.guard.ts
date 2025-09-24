import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const superadminGuard: CanActivateFn = () => {
    const authService = inject(AuthService);
    const router = inject(Router);

    if (!authService.isLoggedIn()) {
        return router.createUrlTree(['/admin/login']);
    }

    if (!authService.isSuperAdmin()) {
        // Redirect to admin dashboard if not superadmin
        return router.createUrlTree(['/admin/dashboard']);
    }

    return true;
};
