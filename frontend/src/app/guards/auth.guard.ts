import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Injectable({
    providedIn: 'root'
})
export class AuthGuard implements CanActivate {
    constructor(private authService: AuthService, private router: Router) { }

    canActivate(): boolean {
        console.log('AuthGuard: Checking authentication status', this.authService.isLoggedIn());
        if (!this.authService.isLoggedIn()) {
            console.log("Redirect to login page");
            this.router.navigate(['/admin/login']);
            return false;
        }
        return true;
    }
}