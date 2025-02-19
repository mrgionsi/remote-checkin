import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environments';

@Injectable({
  providedIn: 'root', // Service is available throughout the app
})
export class ReservationService {
  private apiUrl = `${environment.apiBaseUrl}/api/v1/reservations`;  // Replace with your actual API URL

  constructor(private http: HttpClient) { }

  createReservation(reservation: any): Observable<any> {
    return this.http.post(this.apiUrl, reservation);
  }

  getReservationByStructureId(id: number): Observable<any> {
    return this.http.get(this.apiUrl + '/structure/' + id)
  }

  getMonthlyReservation(id_structure: number): Observable<any> {
    return this.http.get(this.apiUrl + '/monthly/' + id_structure)
  }
  getReservationById(id_structure: number): Observable<any> {
    return this.http.get(this.apiUrl + '/' + id_structure)
  }
}