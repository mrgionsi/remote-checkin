import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { environment } from '../../environments/environments';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class ClientReservationService {

  private apiUrl = `${environment.apiBaseUrl}/api/v1/reservations`;  // Replace with your actual API URL

  constructor(private http: HttpClient, private authService: AuthService) { }

  private checkAuthOrError(): boolean {
    return this.authService.isLoggedIn();
  }

  getClientByReservationId(id_reservation: number): Observable<any> {
    return this.http.get(this.apiUrl + '/' + id_reservation + '/clients')
  }

  getUserPhoto(id_reservation: number, name: string, surname: string, cf: string) {
    if (!this.checkAuthOrError()) {
      return throwError(() => new Error('User not authenticated'));
    }
    return this.http.post(this.apiUrl + '/' + id_reservation + '/client-images', { name, surname, cf })



  }
}
