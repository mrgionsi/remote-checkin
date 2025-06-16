import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

interface AdminLoginResponse {
  access_token: string;
  user: {
    id: number;
    username: string;
    name: string;
    surname: string;
    structures: number[];
    role: string;
  };
}

@Injectable({
  providedIn: 'root'
})
export class AdminLoginService {

  private apiUrl = '/api/v1/admin/login'; // Modifica se necessario

  constructor(private http: HttpClient) { }

  login(username: string, password: string): Observable<AdminLoginResponse> {
    return this.http.post<AdminLoginResponse>(this.apiUrl, { username, password });
  }
}