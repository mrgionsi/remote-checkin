import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { map } from 'rxjs/operators';
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

export interface ActivityResponse {
  items: ActivityItem[];
  pagination?: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

export interface BackgroundJobItem {
  id: number;
  jobType: string;
  status: string;
  attempts: number;
  maxAttempts: number;
  errorMessage: string | null;
  structureId: number | null;
  createdByUserId: number | null;
  createdAt: string;
  availableAt: string;
  finishedAt: string | null;
}

export interface BackgroundJobResponse {
  items: BackgroundJobItem[];
  pagination?: {
    total: number;
    limit: number;
    offset: number;
  };
}

@Injectable({
  providedIn: 'root'
})
export class ActivityService {
  private readonly apiUrl = `${environment.apiBaseUrl}/api/v1/activity/recent`;
  private readonly jobsApiUrl = `${environment.apiBaseUrl}/api/v1/admin/jobs/recent`;

  constructor(private http: HttpClient, private authService: AuthService) {}

  getRecentActivity(
    limit = 20,
    structureId?: number,
    actorRole?: string,
    page = 1,
    actorUserId?: number
  ): Observable<ActivityResponse> {
    if (!this.authService.checkAuthAndRedirect()) {
      return throwError(() => new Error('Authentication failed'));
    }

    const queryParams = new URLSearchParams();
    queryParams.set('limit', String(limit));
    if (structureId !== undefined && structureId !== null) {
      queryParams.set('structure_id', String(structureId));
    }
    if (actorRole) {
      queryParams.set('actor_role', actorRole);
    }
    if (actorUserId !== undefined && actorUserId !== null) {
      queryParams.set('actor_user_id', String(actorUserId));
    }
    queryParams.set('page', String(page));

    const url = `${this.apiUrl}?${queryParams.toString()}`;
    return this.http.get<ActivityResponse>(url, {
      headers: this.authService.getAuthHeaders(),
    });
  }

  getRecentJobs(
    limit = 5,
    status?: string,
    jobType?: string,
    offset = 0
  ): Observable<BackgroundJobResponse> {
    if (!this.authService.checkAuthAndRedirect()) {
      return throwError(() => new Error('Authentication failed'));
    }

    const queryParams = new URLSearchParams();
    queryParams.set('limit', String(limit));
    queryParams.set('offset', String(Math.max(0, offset)));
    if (status) queryParams.set('status', status);
    if (jobType) queryParams.set('jobType', jobType);

    const url = `${this.jobsApiUrl}?${queryParams.toString()}`;
    return this.http.get<any>(url, { headers: this.authService.getAuthHeaders() }).pipe(
      map((response) => {
        const mappedItems = (response?.items || []).map((item: any) => ({
          id: Number(item.id),
          jobType: String(item.job_type || ''),
          status: String(item.status || ''),
          attempts: Number(item.attempts || 0),
          maxAttempts: Number(item.max_attempts || 0),
          errorMessage: item.error_message || null,
          structureId: item.structure_id ?? null,
          createdByUserId: item.created_by_user_id ?? null,
          createdAt: item.created_at || '',
          availableAt: item.available_at || '',
          finishedAt: item.finished_at || null,
        }));

        return {
          items: mappedItems,
          pagination: response?.pagination || { total: 0, limit, offset },
        } as BackgroundJobResponse;
      })
    );
  }
}
