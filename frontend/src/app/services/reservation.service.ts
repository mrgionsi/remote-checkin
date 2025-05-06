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

  // Method to create a reservation
  createReservation(reservation: any): Observable<any> {
    return this.http.post(this.apiUrl, reservation);
  }

  // Method to update a reservation
  updateReservation(reservation: any, reservationId: number): Observable<any> {
    return this.http.patch(this.apiUrl + '/' + reservationId, reservation);
  }

  // Method to get reservations by structure ID
  getReservationByStructureId(id: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/structure/${id}`);
  }

  // Method to get monthly reservations for a structure
  getMonthlyReservation(id_structure: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/monthly/${id_structure}`);
  }

  // Method to get a reservation by its ID
  getReservationById(id_structure: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/${id_structure}`);
  }

  // Method to update reservation status (Approved, Pending, Declined, Sent back to customer)
  updateReservationStatus(reservationId: number, status: any): Observable<any> {
    const url = `${this.apiUrl}/${reservationId}/status`; // URL for updating status
    const body = { status };  // Status field to be updated
    return this.http.put(url, body);  // Send PUT request to the backend API
  }

  deleteReservation(reservationId: number) {
    return this.http.delete(this.apiUrl + '/' + reservationId);
  }
}
