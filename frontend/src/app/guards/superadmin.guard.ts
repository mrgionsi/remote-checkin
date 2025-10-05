import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const superadminGuard: CanActivateFn = () => {
    const authService = inject(AuthService);
    const router = inject(Router);

    if (!authService.isLoggedIn()) {
        router.navigate(['/admin/login']);
        return false;
    }

    if (!authService.isSuperAdmin()) {
        // Redirect to admin dashboard if not superadmin
        router.navigate(['/admin/dashboard']);
        return false;
    }

    return true;
};
