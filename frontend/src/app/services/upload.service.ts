import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environments';

@Injectable({
  providedIn: 'root'
})
export class UploadService {
  private apiUrl = `${environment.apiBaseUrl}/api/v1/upload`;  // API endpoint URL

  constructor(private http: HttpClient) { }

  uploadImages(formData: FormData): Observable<any> {
    return this.http.post(this.apiUrl, formData);
  }
}
