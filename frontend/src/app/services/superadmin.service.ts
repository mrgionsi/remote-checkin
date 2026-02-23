import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';
import { environment } from '../../environments/environments';
import { ActivityResponse } from './activity.service';

export interface Structure {
  id: number;
  name: string;
  street: string;
  city: string;
  cin: string;
  is_active: boolean;
}

export interface User {
  id: number;
  username: string;
  name: string;
  surname: string;
  email: string;
  telephone: string;
  role: string;
  id_role: number;
  structures: Array<{ id: number; name: string }>;
}

export interface Association {
  user_id: number;
  structure_id: number;
  user: {
    id: number;
    username: string;
    name: string;
    surname: string;
  };
  structure: {
    id: number;
    name: string;
    city: string;
  };
}

export interface DashboardData {
  total_structures: number;
  active_structures: number;
  archived_structures: number;
  total_users: number;
  unassigned_admins: number;
  total_reservations: number;
}

export interface PaginationParams {
  page?: number;
  per_page?: number;
  search?: string;
  is_active?: string;
  role?: string;
}

@Injectable({
  providedIn: 'root'
})
export class SuperadminService {
  private baseUrl = `${environment.apiBaseUrl}/api/v1/superadmin`;

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) { }

  private getHeaders(): HttpHeaders {
    return this.authService.getAuthHeaders();
  }

  // Structure Management
  getStructures(params: PaginationParams = {}): Observable<any> {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.set('page', params.page.toString());
    if (params.per_page) queryParams.set('per_page', params.per_page.toString());
    if (params.search) queryParams.set('search', params.search);
    if (params.is_active) queryParams.set('is_active', params.is_active);

    const url = `${this.baseUrl}/structures${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return this.http.get(url, { headers: this.getHeaders() });
  }

  createStructure(structure: Partial<Structure>): Observable<any> {
    return this.http.post(`${this.baseUrl}/structures`, structure, { headers: this.getHeaders() });
  }

  updateStructure(id: number, structure: Partial<Structure>): Observable<any> {
    return this.http.put(`${this.baseUrl}/structures/${id}`, structure, { headers: this.getHeaders() });
  }

  deleteStructure(id: number): Observable<any> {
    return this.http.delete(`${this.baseUrl}/structures/${id}`, { headers: this.getHeaders() });
  }

  restoreStructure(id: number): Observable<any> {
    return this.http.post(`${this.baseUrl}/structures/${id}/restore`, {}, { headers: this.getHeaders() });
  }

  // User Management
  getUsers(params: PaginationParams = {}): Observable<any> {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.set('page', params.page.toString());
    if (params.per_page) queryParams.set('per_page', params.per_page.toString());
    if (params.search) queryParams.set('search', params.search);
    if (params.role) queryParams.set('role', params.role);

    const url = `${this.baseUrl}/users${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return this.http.get(url, { headers: this.getHeaders() });
  }

  createUser(user: Partial<User>): Observable<any> {
    return this.http.post(`${this.baseUrl}/users`, user, { headers: this.getHeaders() });
  }

  updateUser(id: number, user: Partial<User>): Observable<any> {
    return this.http.put(`${this.baseUrl}/users/${id}`, user, { headers: this.getHeaders() });
  }

  resetUserPassword(id: number, password: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/users/${id}/reset-password`, { password }, { headers: this.getHeaders() });
  }

  // Association Management
  getAssociations(userId?: number, structureId?: number): Observable<any> {
    const queryParams = new URLSearchParams();
    if (userId) queryParams.set('user_id', userId.toString());
    if (structureId) queryParams.set('structure_id', structureId.toString());

    const url = `${this.baseUrl}/associations${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return this.http.get(url, { headers: this.getHeaders() });
  }

  createAssociation(userId: number, structureId: number): Observable<any> {
    return this.http.post(`${this.baseUrl}/associations`, { user_id: userId, structure_id: structureId }, { headers: this.getHeaders() });
  }

  deleteAssociation(userId: number, structureId: number): Observable<any> {
    return this.http.delete(`${this.baseUrl}/associations`, {
      headers: this.getHeaders(),
      body: { user_id: userId, structure_id: structureId }
    });
  }

  // Role Management
  getRoles(): Observable<{ roles: any[] }> {
    return this.http.get<{ roles: any[] }>(`${this.baseUrl}/roles`, { headers: this.getHeaders() });
  }

  changeUserRole(userId: number, roleId: number): Observable<any> {
    return this.http.put(`${this.baseUrl}/users/${userId}/change-role`,
      { id_role: roleId },
      { headers: this.getHeaders() }
    );
  }

  // Dashboard
  getDashboardData(): Observable<{ dashboard: DashboardData }> {
    return this.http.get<{ dashboard: DashboardData }>(`${this.baseUrl}/dashboard`, { headers: this.getHeaders() });
  }

  getActivityTimeline(limit = 20, page = 1): Observable<ActivityResponse> {
    return this.http.get<ActivityResponse>(
      `${environment.apiBaseUrl}/api/v1/activity/recent?limit=${limit}&page=${page}`,
      { headers: this.getHeaders() }
    );
  }
}
