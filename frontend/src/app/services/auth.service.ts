import { Injectable } from '@angular/core';
import { HttpHeaders } from '@angular/common/http';

@Injectable({
    providedIn: 'root'
})
export class AuthService {

    getUser() {
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
        if (!token) return false;

        // Decodifica il payload del JWT
        const payload = JSON.parse(atob(token.split('.')[1]));
        const exp = payload.exp;
        const now = Math.floor(Date.now() / 1000);

        return exp && exp > now;
    }

    isLoggedIn(): boolean {
        const user = this.getUser();
        if (!user || !this.isTokenValid()) {
            this.logout(); // Pulisce il localStorage se non valido
            return false;
        }
        return true;
    }

    getUserRole(): string {
        const user = this.getUser();
        return user?.user?.role || '';
    }

    isSuperAdmin(): boolean {
        return this.getUserRole() === 'superadmin';
    }

    logout(): void {
        localStorage.removeItem('user');
        localStorage.removeItem('admin_token');
    }

    getAuthHeaders(): HttpHeaders {
        const token = localStorage.getItem('admin_token');
        console.log(token)
        return new HttpHeaders({
            'Authorization': `Bearer ${token}`
        });
    }
}