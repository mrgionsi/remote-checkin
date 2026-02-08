import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environments';
import { AuthService } from './auth.service';


@Injectable({
  providedIn: 'root',
})
export class RoomService {

  private apiUrl = `${environment.apiBaseUrl}/api/v1/rooms`;  // API endpoint URL

  constructor(private http: HttpClient, private authService: AuthService) { }

  // Fetch all rooms
  getRooms(): Observable<any[]> {
    return this.http.get<any[]>(this.apiUrl, { headers: this.authService.getAuthHeaders() });
  }

  addRoom(room: any): Observable<any> {
    const payload = {
      ...room,
      is_active: room.is_active ?? room.isActive ?? true
    };
    delete payload.isActive;
    return this.http.post<any[]>(this.apiUrl, payload, { headers: this.authService.getAuthHeaders() });
  }
  editRoom(room: any): Observable<any> {
    const payload = {
      ...room,
      is_active: room.is_active ?? room.isActive ?? true
    };
    delete payload.isActive;
    return this.http.put<any[]>(this.apiUrl + '/' + room.id, payload, { headers: this.authService.getAuthHeaders() });
  }
  deleteRoom(idRoom: number): Observable<any> {
    return this.http.delete(this.apiUrl + '/' + idRoom, { headers: this.authService.getAuthHeaders() });
  }
}
