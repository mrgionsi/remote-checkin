import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { FormGroup, FormBuilder, Validators, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { DatePickerModule } from 'primeng/datepicker';
import { CardModule } from 'primeng/card';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { InputGroupModule } from 'primeng/inputgroup';
import { InputGroupAddonModule } from 'primeng/inputgroupaddon';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select'; // Import PrimeNG Select
import { StepperModule } from 'primeng/stepper';
import { UploadIdentityComponent } from '../upload-identity/upload-identity.component';
import { UploadService } from '../services/upload.service';
import { ToastModule } from 'primeng/toast';
import { DialogModule } from 'primeng/dialog';


@Component({
  selector: 'app-remote-checkin',
  standalone: true,
  imports: [StepperModule, UploadIdentityComponent, ToastModule, DialogModule,
    DatePickerModule, InputGroupAddonModule, InputTextModule, CardModule,
    FormsModule, ReactiveFormsModule, InputGroupModule, ButtonModule,
    CommonModule, SelectModule
  ],
  templateUrl: './remote-checkin.component.html',
  styleUrl: './remote-checkin.component.scss',
  providers: [MessageService],

})
export class RemoteCheckinComponent implements OnInit {
  clientForm: FormGroup;
  uploadForm: FormGroup;
  documentTypes = [
    { label: 'Identity Card', value: 'identity_card' },
    { label: 'Driver License', value: 'driver_license' },
    { label: 'Passport', value: 'passport' }
  ];

  languageCode: string | null = '';
  reservationId: string | null = '';
  showConfirmationDialog: boolean = false;

  constructor(private route: ActivatedRoute, private router: Router, private fb: FormBuilder,
    private messageService: MessageService, private uploadService: UploadService) {
    this.uploadForm = this.fb.group({
      frontImage: [null, Validators.required],
      backImage: [null, Validators.required],
      selfie: [null, Validators.required]
    });
    this.clientForm = this.fb.group({
      name: ['', Validators.required],
      surname: ['', Validators.required],
      birthday: ['', Validators.required],
      street: ['', Validators.required],
      number_city: ['', Validators.required],
      city: ['', Validators.required],
      province: ['', Validators.required],
      cap: ['', [Validators.required, Validators.pattern('^[0-9]{5}$')]],
      telephone: ['', [Validators.required, Validators.pattern('^[0-9]+$')]],
      document_type: ['', Validators.required],  // New field
      document_number: ['', Validators.required],
      cf: ['', [Validators.required, Validators.pattern('^[A-Z0-9]{16}$')]],
    });
  }

  ngOnInit() {


    this.languageCode = this.route.snapshot.paramMap.get('code');
    this.route.params.subscribe(params => {
      if (!params['id']) {
        this.router.navigate(['/reservation-check', params['code']]);
      } else {
        this.reservationId = this.route.snapshot.paramMap.get('id');
      }
    });
  }


  // Method to handle FormData received from the child
  handleFormData(formData: FormGroup) {
    // Here you can do anything with the received FormData
    this.uploadForm = formData;
    console.log(this.uploadForm.get('frontImage'))
    /*     this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Images uploaded successfully'
        }); */
  }

  uploadReservationData() {
    console.log("uploadReservationData called");  // For debugging

    if (this.uploadForm.invalid || this.clientForm.invalid) {
      this.messageService.add({ severity: 'error', summary: 'Error', detail: 'All fields and images are required' });
      return;
    }

    const formData = new FormData();

    // Append image files
    formData.append('frontImage', this.uploadForm.get('frontImage')?.value);
    formData.append('backImage', this.uploadForm.get('backImage')?.value);
    formData.append('selfie', this.uploadForm.get('selfie')?.value);

    // Fetch additional data from clientForm
    const formFields = [
      'name', 'surname', 'birthday', 'street', 'number_city',
      'city', 'province', 'cap', 'telephone', 'document_type',
      'document_number', 'cf'
    ];

    formFields.forEach(field => {
      let value = this.clientForm.get(field)?.value;

      // If the field is 'birthday', format it to 'YYYY-MM-DD' to ensure compliance
      if (field === 'birthday' && value) {
        value = value instanceof Date ? value.toISOString().split('T')[0] : value; // Format as 'YYYY-MM-DD'
      }

      if (value) formData.append(field, value);
    });

    // Append reservationId separately
    if (this.reservationId) {
      formData.append('reservationId', this.reservationId.toString());
    }

    this.uploadService.uploadImages(formData).subscribe({
      next: (response) => {
        // Show success message with API response
        console.log(response)
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: response.message || 'Images uploaded successfully'
        });
        this.showConfirmationDialog = true;
      },
      error: (error) => {
        // Handle error response
        console.log(error)
        const errorMessage = error.error?.error || 'Upload failed';

        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: errorMessage
        });
      }
    });

  }
  closeDialog() {
  }

}
