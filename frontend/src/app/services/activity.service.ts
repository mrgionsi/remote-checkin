import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { environment } from '../../environments/environments';
import { AuthService } from './auth.service';

export interface ActivityItem {
  id: number;
  eventType: string;
  entityType: string;
  entityId: number | null;
  structureId: number | null;
  actorUserId: number | null;
  actorRole: string | null;
  description: string;
  metadata: Record<string, unknown>;
  createdAt: string;
}

@Injectable({
  providedIn: 'root'
})
export class ActivityService {
  private readonly apiUrl = `${environment.apiBaseUrl}/api/v1/activity/recent`;

  constructor(private http: HttpClient, private authService: AuthService) {}

  getRecentActivity(limit = 20, structureId?: number): Observable<{ items: ActivityItem[] }> {
    if (!this.authService.checkAuthAndRedirect()) {
      return throwError(() => new Error('Authentication failed'));
    }

    const queryParams = new URLSearchParams();
    queryParams.set('limit', String(limit));
    if (structureId !== undefined && structureId !== null) {
      queryParams.set('structure_id', String(structureId));
    }

    const url = `${this.apiUrl}?${queryParams.toString()}`;
    return this.http.get<{ items: ActivityItem[] }>(url, {
      headers: this.authService.getAuthHeaders(),
    });
  }
}
