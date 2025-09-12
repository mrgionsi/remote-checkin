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
import { DocumentTypeLabelPipe } from '../pipes/document-type-label.pipe';
import { TranslocoPipe, TranslocoService } from '@jsverse/transloco';
import { ReservationService } from '../services/reservation.service';
import { HttpClient } from '@angular/common/http';


@Component({
  selector: 'app-remote-checkin',
  standalone: true,
  imports: [StepperModule, UploadIdentityComponent, ToastModule, DialogModule,
    DatePickerModule, InputGroupAddonModule, InputTextModule, CardModule,
    FormsModule, ReactiveFormsModule, InputGroupModule, ButtonModule,
    CommonModule, SelectModule, DocumentTypeLabelPipe, TranslocoPipe
  ],
  templateUrl: './remote-checkin.component.html',
  styleUrl: './remote-checkin.component.scss',
  providers: [MessageService],

})
export class RemoteCheckinComponent implements OnInit {
  clientForm: FormGroup;
  uploadForm: FormGroup;
  documentTypes = [{}];

  // Portale Alloggi options
  genderOptions = [
    { label: 'Male', value: '1' },
    { label: 'Female', value: '2' }
  ];

  // Reference data loaded from JSON files
  countryOptions: any[] = [];
  provinceOptions: any[] = [];
  municipalityOptions: any[] = [];

  languageCode: string | null = '';
  reservationId: string | null = '';
  showConfirmationDialog: boolean = false;
  reservationDetails: any = null;
  registeredClientsCount: number = 0;
  canRegister: boolean = true;

  constructor(private route: ActivatedRoute, private router: Router, private fb: FormBuilder,
    private readonly messageService: MessageService, private uploadService: UploadService,
    private readonly translocoService: TranslocoService, private reservationService: ReservationService,
    private http: HttpClient
  ) {
    this.uploadForm = this.fb.group({
      frontimage: [null, Validators.required],
      backimage: [null, Validators.required],
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
      document_type: ['', Validators.required],
      document_number: ['', Validators.required],
      cf: ['', [Validators.required, Validators.pattern('^[A-Z0-9]{16}$')]],

      // Portale Alloggi required fields
      sesso: ['', Validators.required],
      nazionalita: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      comune_nascita: ['', Validators.required],
      provincia_nascita: ['', Validators.required],
      stato_nascita: ['', Validators.required],
      cittadinanza: ['', Validators.required],
      luogo_emissione: ['', Validators.required],
      data_emissione: ['', Validators.required],
      data_scadenza: ['', Validators.required],
      autorita_rilascio: ['', Validators.required],
      comune_residenza: ['', Validators.required],
      provincia_residenza: ['', Validators.required],
      stato_residenza: ['', Validators.required],
    });
  }

  ngOnInit() {
    this.documentTypes = [
      { label: this.translocoService.translate('identity-card-label'), value: 'identity_card' },
      { label: this.translocoService.translate('driver-license-label'), value: 'driver_license' },
      { label: this.translocoService.translate('passport-label'), value: 'passport' }
    ];

    // Load reference data from JSON files
    this.loadReferenceData();

    this.languageCode = this.route.snapshot.paramMap.get('code');
    this.route.params.subscribe(params => {
      if (!params['id']) {
        this.router.navigate(['/reservation-check', params['code']]);
      } else {
        this.reservationId = this.route.snapshot.paramMap.get('id');
        // Load reservation details and check capacity
        this.loadReservationDetails();
      }
    });
  }

  // Method to load reservation details and check capacity
  loadReservationDetails() {
    if (!this.reservationId) return;

    this.reservationService.getReservationById(this.reservationId).subscribe({
      next: (reservation) => {
        this.reservationDetails = reservation;
        this.checkRegistrationCapacity();
      },
      error: (error) => {
        console.warn('Error loading reservation details:', error);

        // Block registration when capacity cannot be verified
        this.canRegister = false;
        this.disableFormControls();

        this.messageService.add({
          severity: 'warn',
          summary: this.translocoService.translate('registration-unavailable'),
          detail: this.translocoService.translate('capacity-verification-failed')
        });
      }
    });
  }

  // Method to check if registration is still available
  checkRegistrationCapacity() {
    if (!this.reservationDetails) return;

    // Use the data already returned from the reservation check
    this.registeredClientsCount = this.reservationDetails.registered_clients_count || 0;

    // Safely coerce number_of_people to numeric type
    const rawMaxPeople = this.reservationDetails.number_of_people;
    const maxPeople = Number(rawMaxPeople) || 1;

    if (this.registeredClientsCount >= maxPeople) {
      this.canRegister = false;
      this.disableFormControls();
      this.messageService.add({
        severity: 'warn',
        summary: this.translocoService.translate('registration-full'),
        detail: this.translocoService.translate('reservation-capacity-status', {
          registered: this.registeredClientsCount,
          max: maxPeople
        })
      });
    } else {
      this.canRegister = true;
      this.enableFormControls();
    }
  }

  // Method to disable all form controls when registration is full
  private disableFormControls() {
    this.clientForm.disable();
    this.uploadForm.disable();
  }

  // Method to enable all form controls when registration is available
  private enableFormControls() {
    this.clientForm.enable();
    this.uploadForm.enable();
  }

  // Load reference data from JSON files
  private loadReferenceData() {
    // Load countries
    this.http.get<any[]>('/assets/data/countries.json').subscribe({
      next: (countries) => {
        this.countryOptions = countries;
      },
      error: (error) => {
        console.error('Error loading countries:', error);
        // Fallback to basic countries
        this.countryOptions = [
          { label: 'Italy', value: 'IT' },
          { label: 'United States', value: 'US' },
          { label: 'United Kingdom', value: 'GB' },
          { label: 'Other', value: 'XX' }
        ];
      }
    });

    // Load Italian provinces
    this.http.get<any[]>('/assets/data/italian-provinces.json').subscribe({
      next: (provinces) => {
        this.provinceOptions = provinces;
      },
      error: (error) => {
        console.error('Error loading provinces:', error);
        // Fallback to basic provinces
        this.provinceOptions = [
          { label: 'Roma (RM)', value: 'RM' },
          { label: 'Milano (MI)', value: 'MI' },
          { label: 'Napoli (NA)', value: 'NA' },
          { label: 'Torino (TO)', value: 'TO' }
        ];
      }
    });

    // Load Italian municipalities
    this.http.get<any[]>('/assets/data/italian-municipalities.json').subscribe({
      next: (municipalities) => {
        this.municipalityOptions = municipalities;
      },
      error: (error) => {
        console.error('Error loading municipalities:', error);
        // Fallback to basic municipalities
        this.municipalityOptions = [
          { label: 'Roma', value: 'H501' },
          { label: 'Milano', value: 'F205' },
          { label: 'Napoli', value: 'F839' },
          { label: 'Torino', value: 'L219' }
        ];
      }
    });
  }

  // Method to handle FormData received from the child
  handleFormData(formData: FormGroup) {
    // Here you can do anything with the received FormData
    this.uploadForm = formData;
    console.log(this.uploadForm.get('frontimage'))
    /*     this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Images uploaded successfully'
        }); */
  }

  uploadReservationData() {
    console.log("uploadReservationData called");  // For debugging

    // Check if registration is still available
    if (!this.canRegister) {
      this.messageService.add({
        severity: 'warn',
        summary: this.translocoService.translate('registration-full'),
        detail: this.translocoService.translate('reservation-full-message')
      });
      return;
    }

    if (this.uploadForm.invalid || this.clientForm.invalid) {
      this.messageService.add({ severity: 'error', summary: 'Error', detail: 'All fields and images are required' });
      return;
    }

    const formData = new FormData();

    // Append image files
    formData.append('frontimage', this.uploadForm.get('frontimage')?.value);
    formData.append('backimage', this.uploadForm.get('backimage')?.value);
    formData.append('selfie', this.uploadForm.get('selfie')?.value);

    // Fetch additional data from clientForm
    const formFields = [
      'name', 'surname', 'birthday', 'street', 'number_city',
      'city', 'province', 'cap', 'telephone', 'document_type',
      'document_number', 'cf',
      // Portale Alloggi required fields
      'sesso', 'nazionalita', 'email', 'comune_nascita',
      'provincia_nascita', 'stato_nascita', 'cittadinanza',
      'luogo_emissione', 'data_emissione', 'data_scadenza',
      'autorita_rilascio', 'comune_residenza', 'provincia_residenza', 'stato_residenza'
    ];

    formFields.forEach(field => {
      let value = this.clientForm.get(field)?.value;

      // If the field is a date field, format it to 'YYYY-MM-DD' to ensure compliance
      if (['birthday', 'data_emissione', 'data_scadenza'].includes(field) && value) {
        if (value instanceof Date) {
          // Use local timezone to avoid day shift issues
          value = this.formatDateToLocalString(value);
        }
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

  /**
   * Format a Date object to YYYY-MM-DD string using local timezone
   * This avoids timezone shift issues that occur with toISOString()
   */
  private formatDateToLocalString(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  closeDialog() {
  }

}
