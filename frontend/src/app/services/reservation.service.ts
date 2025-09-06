import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { throwError, Observable } from 'rxjs';
import { environment } from '../../environments/environments';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root',
})
export class ReservationService {
  private apiUrl = `${environment.apiBaseUrl}/api/v1/reservations`;

  constructor(private http: HttpClient, private authService: AuthService) { }

  private checkAuthOrError(): boolean {
    return this.authService.isLoggedIn();
  }

  createReservation(reservation: any): Observable<any> {
    if (!this.checkAuthOrError()) {
      return throwError(() => new Error('User not authenticated'));
    }
    return this.http.post(this.apiUrl, reservation, { headers: this.authService.getAuthHeaders() });
  }

  updateReservation(reservation: any, reservationId: number): Observable<any> {
    if (!this.checkAuthOrError()) {
      return throwError(() => new Error('User not authenticated'));
    }
    return this.http.patch(this.apiUrl + '/' + reservationId, reservation, { headers: this.authService.getAuthHeaders() });
  }

  getReservationByStructureId(id: number): Observable<any> {
    if (!this.checkAuthOrError()) {
      return throwError(() => new Error('User not authenticated'));
    }
    return this.http.get(
      `${this.apiUrl}/structure/${id}`,
      { headers: this.authService.getAuthHeaders() }
    );
  }

  getMonthlyReservation(id_structure: number): Observable<any> {
    if (!this.checkAuthOrError()) {
      return throwError(() => new Error('User not authenticated'));
    }
    return this.http.get(`${this.apiUrl}/monthly/${id_structure}`, { headers: this.authService.getAuthHeaders() });
  }

  getReservationById(reservation_reference: string): Observable<any> {
    // This endpoint is public, so we do not check authentication
    return this.http.get(`${this.apiUrl}/check/${reservation_reference}`);
  }
  checkReservationById(id_reference: string): Observable<any> {
    // This endpoint is public, so we do not check authentication
    return this.http.get(`${this.apiUrl}/check/${id_reference}`,);
  }
  getAdminReservationById(id_structure: number): Observable<any> {
    if (!this.checkAuthOrError()) {
      return throwError(() => new Error('User not authenticated'));
    }
    return this.http.get(`${this.apiUrl}/admin/${id_structure}`, { headers: this.authService.getAuthHeaders() });
  }

  updateReservationStatus(reservationId: number, status: any): Observable<any> {
    if (!this.checkAuthOrError()) {
      return throwError(() => new Error('User not authenticated'));
    }
    const url = `${this.apiUrl}/${reservationId}/status`;
    const body = { status };
    return this.http.put(url, body, { headers: this.authService.getAuthHeaders() });
  }

  deleteReservation(reservationId: number): Observable<any> {
    if (!this.checkAuthOrError()) {
      return throwError(() => new Error('User not authenticated'));
    }
    return this.http.delete(this.apiUrl + '/' + reservationId, { headers: this.authService.getAuthHeaders() });
  }

  getClientsByReservationId(reservationId: number): Observable<any> {
    // This endpoint is public, so we do not check authentication
    return this.http.get(`${this.apiUrl}/${reservationId}/clients`);
  }
}
