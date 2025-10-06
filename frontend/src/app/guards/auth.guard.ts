import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = () => {
    const authService = inject(AuthService);
    const router = inject(Router);

    // Check if user is logged in without redirecting
    if (!authService.isLoggedIn()) {
        router.navigate(['/admin/login']);
        return false;
    }
    return true;
};