import { Injectable } from '@angular/core';
import { HttpHeaders } from '@angular/common/http';
import { BehaviorSubject } from 'rxjs';
import { Router } from '@angular/router';

@Injectable({
    providedIn: 'root'
})
export class AuthService {
    private userSubject = new BehaviorSubject<any>(this.getInitialUser());
    user$ = this.userSubject.asObservable();
    private isInitialized = false;

    constructor(private router: Router) {
        // Initialize user state from localStorage on service creation
        this.initializeAuthState();
    }

    private getInitialUser(): any {
        if (typeof window === 'undefined' || !window.localStorage) return null;

        const user = this.getUser();
        const token = localStorage.getItem('admin_token');

        if (user && token && this.isTokenValid()) {
            return user;
        }
        return null;
    }

    private initializeAuthState(): void {
        if (typeof window === 'undefined' || !window.localStorage) {
            this.isInitialized = true;
            return;
        }

        const user = this.getUser();
        const token = localStorage.getItem('admin_token');

        if (user && token && this.isTokenValid()) {
            this.userSubject.next(user);
        } else {
            // Clear invalid state
            this.clearUser();
        }

        this.isInitialized = true;
    }

    setUser(user: any) {
        localStorage.setItem('user', JSON.stringify(user));
        this.userSubject.next(user);
    }

    clearUser() {
        localStorage.removeItem('user');
        localStorage.removeItem('admin_token');
        this.userSubject.next(null);
    }

    getUser() {
        if (typeof window === 'undefined' || !window.localStorage) return null;
        const userStr = localStorage.getItem('user');
        if (!userStr) return null;
        try {
            return JSON.parse(userStr);
        } catch {
            return null;
        }
    }

    isTokenValid(): boolean {
        const token = localStorage.getItem('admin_token');
        if (!token) {
            return false;
        }

        try {
            // Decodifica il payload del JWT
            const payload = JSON.parse(atob(token.split('.')[1]));
            const exp = payload.exp;
            const now = Math.floor(Date.now() / 1000);

            return exp && exp > now;
        } catch (error) {
            console.error('Invalid JWT token:', error);
            return false;
        }
    }

    isLoggedIn(): boolean {
        // Check if we're in a browser environment
        if (typeof window === 'undefined') {
            return false;
        }

        // Check if localStorage is available
        if (!window.localStorage) {
            return false;
        }

        const user = this.getUser();
        const tokenValid = this.isTokenValid();

        return !!(user && tokenValid);
    }

    checkAuthAndRedirect(): boolean {
        if (!this.isInitialized) {
            // Wait for initialization
            return false;
        }
        if (!this.isLoggedIn()) {
            this.logout();
            this.router.navigate(['/admin/login']);
            return false;
        }
        return true;
    }

    getUserRole(): string {
        const user = this.getUser();
        return user?.role || '';
    }

    isSuperAdmin(): boolean {
        return this.getUserRole() === 'superadmin';
    }

    logout(): void {
        localStorage.removeItem('user');
        localStorage.removeItem('admin_token');
    }

    getAuthHeaders(): HttpHeaders {
        // Guard for SSR where window/localStorage are not available
        if (typeof window === 'undefined' || !window.localStorage) {
            return new HttpHeaders();
        }

        const token = localStorage.getItem('admin_token');
        return token
            ? new HttpHeaders({ 'Authorization': `Bearer ${token}` })
            : new HttpHeaders();
    }
}