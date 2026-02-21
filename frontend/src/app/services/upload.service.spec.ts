import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { UploadService } from './upload.service';
import { environment } from '../../environments/environments';

describe('UploadService', () => {
  let service: UploadService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()]
    });
    service = TestBed.inject(UploadService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should send upload token header when provided', () => {
    const formData = new FormData();
    formData.append('foo', 'bar');

    service.uploadImages(formData, 'upload-token').subscribe();

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/upload`);
    expect(req.request.method).toBe('POST');
    expect(req.request.headers.get('X-Upload-Token')).toBe('upload-token');
    req.flush({ ok: true });
  });

  it('should send document validation token header when provided', () => {
    const formData = new FormData();
    formData.append('foo', 'bar');

    service.uploadImages(formData, 'upload-token', 'doc-validation-token').subscribe();

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/upload`);
    expect(req.request.method).toBe('POST');
    expect(req.request.headers.get('X-Upload-Token')).toBe('upload-token');
    expect(req.request.headers.get('X-Document-Validation-Token')).toBe('doc-validation-token');
    req.flush({ ok: true });
  });

  it('should call validate documents endpoint', () => {
    const formData = new FormData();
    formData.append('foo', 'bar');

    service.validateDocuments(formData, 'upload-token').subscribe();

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/upload/validate-documents`);
    expect(req.request.method).toBe('POST');
    expect(req.request.headers.get('X-Upload-Token')).toBe('upload-token');
    req.flush({ ok: true });
  });
});
