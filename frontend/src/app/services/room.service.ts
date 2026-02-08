import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environments';
import { AuthService } from './auth.service';


@Injectable({
  providedIn: 'root',
})
export class RoomService {

  private apiUrl = `${environment.apiBaseUrl}/api/v1/rooms`;  // API endpoint URL
  private readonly authService = inject(AuthService);

  constructor(private http: HttpClient) { }

  // Fetch all rooms
  getRooms(structureId?: number | null): Observable<any[]> {
    const params: any = {};
    if (structureId) {
      params.structure_id = structureId;
    }
    return this.http.get<any[]>(this.apiUrl, { headers: this.authService.getAuthHeaders(), params });
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
