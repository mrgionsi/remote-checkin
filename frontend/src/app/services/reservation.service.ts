import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environments';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root',
})
export class ReservationService {
  private apiUrl = `${environment.apiBaseUrl}/api/v1/reservations`;

  constructor(private http: HttpClient, private authService: AuthService) { }

  createReservation(reservation: any): Observable<any> {
    return this.http.post(this.apiUrl, reservation, { headers: this.authService.getAuthHeaders() });
  }

  updateReservation(reservation: any, reservationId: number): Observable<any> {
    return this.http.patch(this.apiUrl + '/' + reservationId, reservation, { headers: this.authService.getAuthHeaders() });
  }

  getReservationByStructureId(id: number): Observable<any> {
    return this.http.get(
      `${this.apiUrl}/structure/${id}`,
      { headers: this.authService.getAuthHeaders() }
    );
  }

  getMonthlyReservation(id_structure: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/monthly/${id_structure}`, { headers: this.authService.getAuthHeaders() });
  }

  getReservationById(id_structure: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/${id_structure}`, { headers: this.authService.getAuthHeaders() });
  }

  updateReservationStatus(reservationId: number, status: any): Observable<any> {
    const url = `${this.apiUrl}/${reservationId}/status`;
    const body = { status };
    return this.http.put(url, body, { headers: this.authService.getAuthHeaders() });
  }

  deleteReservation(reservationId: number) {
    return this.http.delete(this.apiUrl + '/' + reservationId, { headers: this.authService.getAuthHeaders() });
  }
}
