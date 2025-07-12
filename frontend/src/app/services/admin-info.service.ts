import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';
import { environment } from '../../environments/environments';

@Injectable({
    providedIn: 'root'
})
export class AdminInfoService {
    private apiUrl = `${environment.apiBaseUrl}/api/v1/admin/me`;

    constructor(private http: HttpClient, private authService: AuthService) { }

    getAdminInfo(): Observable<any> {
        return this.http.get(this.apiUrl, { headers: this.authService.getAuthHeaders() });
    }
}