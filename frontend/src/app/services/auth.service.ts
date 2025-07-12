import { Injectable } from '@angular/core';

@Injectable({
    providedIn: 'root'
})
export class AuthService {

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
        const user = this.getUser();
        const token = user?.token;
        if (!token) return false;

        // Decodifica il payload del JWT
        const payload = JSON.parse(atob(token.split('.')[1]));
        const exp = payload.exp;
        const now = Math.floor(Date.now() / 1000);

        return exp && exp > now;
    }

    isLoggedIn(): boolean {
        return !!this.getUser() && this.isTokenValid();
    }

    getUserRole(): string {
        const user = this.getUser();
        return user?.user?.role || '';
    }

    isSuperAdmin(): boolean {
        return this.getUserRole() === 'superadmin';
    }
}