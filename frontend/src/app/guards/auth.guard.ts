import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = () => {
    const authService = inject(AuthService);
    const router = inject(Router);

    console.log('AuthGuard is checking if user is logged in');
    console.log(authService.isLoggedIn());
    if (!authService.isLoggedIn()) {

        console.log('User is not logged in, redirecting to login page');
        //return router.createUrlTree(['/admin/login']);
        return false;
    }
    return true;

};