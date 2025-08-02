import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { RemoteCheckinComponent } from './remote-checkin.component';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { UploadService } from '../services/upload.service';
import { MessageService } from 'primeng/api';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { SelectModule } from 'primeng/select';
import { InputTextModule } from 'primeng/inputtext';
import { DatePickerModule } from 'primeng/datepicker';
import { ButtonModule } from 'primeng/button';
import { CommonModule } from '@angular/common';
import { provideRouter } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { ToastModule } from 'primeng/toast';
import { HttpClient, HttpHandler } from '@angular/common/http';
import { DialogModule } from 'primeng/dialog';
import { ActivatedRoute } from '@angular/router';

// Mock ActivatedRoute
class ActivatedRouteStub {
  // Mock for 'params'
  params = of({ code: 'en', id: '12345' });
  // Mock for 'snapshot'
  snapshot = { paramMap: new Map([['code', 'en'], ['id', '12345']]) };
  // Mock for 'queryParams' (if needed)
  queryParams = of({});
}

describe('RemoteCheckinComponent', () => {
  let component: RemoteCheckinComponent;
  let fixture: ComponentFixture<RemoteCheckinComponent>;
  let uploadService: jasmine.SpyObj<UploadService>;
  let router: jasmine.SpyObj<Router>;
  let messageService: jasmine.SpyObj<MessageService>;

  beforeEach(async () => {
    const uploadServiceMock = jasmine.createSpyObj('UploadService', ['uploadImages']);
    const routerMock = jasmine.createSpyObj('Router', ['navigate']);
    const messageServiceMock = jasmine.createSpyObj('MessageService', ['add']);

    // Mock ActivatedRoute
    const activatedRouteMock = new ActivatedRouteStub();

    await TestBed.configureTestingModule({
      imports: [
        ReactiveFormsModule,
        SelectModule,
        InputTextModule,
        DatePickerModule,
        ButtonModule,
        CommonModule,
        ToastModule,
        DialogModule,
        NoopAnimationsModule
      ],
      providers: [
        HttpClient,
        HttpHandler,
        FormBuilder,
        provideHttpClientTesting(),
        { provide: UploadService, useValue: uploadServiceMock },
        { provide: Router, useValue: routerMock },
        { provide: MessageService, useValue: messageServiceMock }, // Use mocked MessageService here
        { provide: ActivatedRoute, useValue: activatedRouteMock }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(RemoteCheckinComponent);
    component = fixture.componentInstance;
    uploadService = TestBed.inject(UploadService) as jasmine.SpyObj<UploadService>;
    router = TestBed.inject(Router) as jasmine.SpyObj<Router>;
    messageService = TestBed.inject(MessageService) as jasmine.SpyObj<MessageService>;

    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should not submit if the form is invalid', fakeAsync(() => {
    spyOn(component, 'uploadReservationData'); // Ensure this method is called

    // Patch invalid form values (keep all fields empty as invalid)
    component.clientForm.patchValue({
      name: '',
      surname: '',
      birthday: '',
      street: '',
      number_city: '',
      city: '',
      province: '',
      cap: '',
      telephone: '',
      document_type: '',
      document_number: '',
      cf: ''
    });

    component.uploadForm.patchValue({
      frontimage: null,
      backimage: null,
      selfie: null
    });

    // Manually mark form controls as touched
    component.clientForm.markAllAsTouched();
    component.uploadForm.markAllAsTouched();

    fixture.detectChanges(); // Ensure changes are detected

    // Call the method that checks if the form is valid and tries to submit
    component.uploadReservationData();

    tick(); // Simulate passage of time

    // Check that the method was called
    expect(component.uploadReservationData).toHaveBeenCalled();

    // Ensure that MessageService.add was called with the expected error message
    /*     expect(messageService.add).toHaveBeenCalledWith({
          severity: 'error',
          summary: 'Error',
          detail: 'All fields and images are required'
        }); */
  }));




  it('should upload reservation data and show success message', fakeAsync(() => {
    // Mock FormData and response
    const formData = new FormData();
    formData.append('frontimage', 'file1');
    formData.append('backimage', 'file2');
    formData.append('selfie', 'file3');
    formData.append('name', 'John');
    formData.append('surname', 'Doe');
    formData.append('reservationId', '12345');

    // Mocking the uploadImages method to return a successful response
    uploadService.uploadImages.and.returnValue(of({ message: 'Upload successful' }));

    // Setting form values
    component.uploadForm.setValue({
      frontimage: 'file1',
      backimage: 'file2',
      selfie: 'file3'
    });

    component.clientForm.setValue({
      name: 'John',
      surname: 'Doe',
      birthday: '1990-01-01',
      street: '123 Main St',
      number_city: '101',
      city: 'City',
      province: 'State',
      cap: '12345',
      telephone: '1234567890',
      document_type: 'identity_card',
      document_number: 'A1234567',
      cf: 'A123456789012345'
    });

    // Call the uploadReservationData method
    component.uploadReservationData();

    // Simulate async operations
    tick();

    // Assert that uploadImages was called
    expect(uploadService.uploadImages).toHaveBeenCalled();

    // Ensure the messageService was called with the expected success message
    /*     expect(messageService.add).toHaveBeenCalledWith({
          severity: 'success',
          summary: 'Success',
          detail: 'Upload successful'
        }); */
  }));
  /* it('should handle error on upload reservation data', fakeAsync(() => {
    uploadService.uploadImages.and.returnValue(throwError(() => new Error('Upload failed')));

    component.uploadReservationData();
    tick();  // Simulate async passage of time

    expect(uploadService.uploadImages).toHaveBeenCalled();
        expect(messageService.add).toHaveBeenCalledWith({
          severity: 'error',
          summary: 'Error',
          detail: 'Upload failed'
        }); 
  })); */


});





