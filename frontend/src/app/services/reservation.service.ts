import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root', // Service is available throughout the app
})
export class ReservationService {
  private apiUrl = 'https://your-api-endpoint/reservations';  // Replace with your actual API URL

  constructor(private http: HttpClient) { }

  createReservation(reservation: any): Observable<any> {
    return this.http.post(this.apiUrl, reservation);
  }
}