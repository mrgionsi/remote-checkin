import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environments';

@Injectable({
  providedIn: 'root'
})
export class UploadService {
  private apiUrl = `${environment.apiBaseUrl}/api/v1/upload`;  // API endpoint URL
  private validateApiUrl = `${environment.apiBaseUrl}/api/v1/upload/validate-documents`;

  constructor(private http: HttpClient) { }

  uploadImages(
    formData: FormData,
    uploadToken?: string | null,
    documentValidationToken?: string | null
  ): Observable<any> {
    let headers = new HttpHeaders();
    if (uploadToken) {
      headers = headers.set('X-Upload-Token', uploadToken);
    }
    if (documentValidationToken) {
      headers = headers.set('X-Document-Validation-Token', documentValidationToken);
    }
    return this.http.post(this.apiUrl, formData, { headers: headers.keys().length ? headers : undefined });
  }

  validateDocuments(formData: FormData, uploadToken?: string | null): Observable<any> {
    const headers = uploadToken
      ? new HttpHeaders({ 'X-Upload-Token': uploadToken })
      : undefined;
    return this.http.post(this.validateApiUrl, formData, { headers });
  }
}
