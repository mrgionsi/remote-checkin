import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environments'; // Adjust if necessary


@Injectable({
  providedIn: 'root',
})
export class RoomService {

  private apiUrl = `${environment.apiBaseUrl}/api/v1/rooms`;  // API endpoint URL

  constructor(private http: HttpClient) { }

  // Fetch all rooms
  getRooms(): Observable<any[]> {
    return this.http.get<any[]>(this.apiUrl);
  }
}