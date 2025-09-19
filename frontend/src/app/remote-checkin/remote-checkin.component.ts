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
import { TranslocoPipe, TranslocoService } from '@jsverse/transloco';
import { ReservationService } from '../services/reservation.service';
import { HttpClient } from '@angular/common/http';
import {
  FALLBACK_MUNICIPALITY_OPTIONS,
  FALLBACK_MUNICIPALITY_MAPPINGS,
  FALLBACK_DOCUMENT_TYPE_OPTIONS,
  FALLBACK_DOCUMENT_TYPE_MAPPINGS,
  FALLBACK_COUNTRY_OPTIONS,
  FALLBACK_COUNTRY_MAPPINGS
} from '../shared/constants/fallback-data';


@Component({
  selector: 'app-remote-checkin',
  standalone: true,
  imports: [StepperModule, UploadIdentityComponent, ToastModule, DialogModule,
    DatePickerModule, InputGroupAddonModule, InputTextModule, CardModule,
    FormsModule, ReactiveFormsModule, InputGroupModule, ButtonModule,
    CommonModule, SelectModule, TranslocoPipe
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
  genderOptions: { label: string; value: string }[] = [];

  // Reference data loaded from JSON files
  countryOptions: any[] = [];
  provinceOptions: any[] = [];
  municipalityOptions: any[] = [];
  documentTypeOptions: any[] = [];
  luogoEmissioneOptions: any[] = [];

  // Mapping data for display
  countryMappings: { [key: string]: string } = {};
  municipalityMappings: { [key: string]: string } = {};
  documentTypeMappings: { [key: string]: string } = {};
  luogoEmissioneMappings: { [key: string]: string } = {};
  provinceMappings: { [key: string]: string } = {};

  // Performance optimization flags
  private dataLoaded = false;
  private loadingPromise: Promise<void> | null = null;
  public isLoadingData = true;
  public loadingLuogoEmissioneOptions = false;
  public isSubmitting = false;


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
      cap: ['', [Validators.required, Validators.pattern('^[0-9]{5}$')]],
      telephone: ['', [Validators.required, Validators.pattern('^[0-9]+$')]],
      document_type: ['', Validators.required],
      document_number: ['', Validators.required],
      cf: ['', [Validators.required, Validators.pattern('^[A-Z0-9]{16}$')]],

      // Portale Alloggi required fields
      sesso: ['', Validators.required],
      nazionalita: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      comune_nascita_code: [''], // Hidden field for the municipality code
      provincia_nascita: ['', Validators.required],
      stato_nascita: ['', Validators.required],
      cittadinanza: ['', Validators.required],
      luogo_emissione: ['', Validators.required],
      data_emissione: ['', Validators.required],
      data_scadenza: ['', Validators.required],
      autorita_rilascio: ['', Validators.required],
      comune_residenza_code: [''], // Hidden field for the municipality code
      provincia_residenza: ['', Validators.required],
      stato_residenza: ['', Validators.required],
    }, { validators: this.documentDateValidator });
  }

  // Custom validator to ensure document expiry date is after issue date
  documentDateValidator(form: FormGroup) {
    const issueDate = form.get('data_emissione')?.value;
    const expiryDate = form.get('data_scadenza')?.value;

    if (!issueDate || !expiryDate) {
      return null; // Don't validate if either date is missing
    }

    try {
      // Convert to Date objects if they're strings
      let issue: Date;
      let expiry: Date;

      if (issueDate instanceof Date) {
        issue = issueDate;
      } else if (typeof issueDate === 'string') {
        // Handle different date formats
        issue = new Date(issueDate);
      } else {
        return null; // Invalid date format
      }

      if (expiryDate instanceof Date) {
        expiry = expiryDate;
      } else if (typeof expiryDate === 'string') {
        // Handle different date formats
        expiry = new Date(expiryDate);
      } else {
        return null; // Invalid date format
      }

      // Check if dates are valid
      if (isNaN(issue.getTime()) || isNaN(expiry.getTime())) {
        return null; // Invalid dates
      }

      // Set time to start of day for accurate comparison
      issue.setHours(0, 0, 0, 0);
      expiry.setHours(0, 0, 0, 0);

      // Check if expiry date is after issue date (not equal or before)
      if (expiry <= issue) {
        return { documentDateInvalid: true };
      }

      return null;
    } catch (error) {
      console.error('Error in date validation:', error);
      return null; // Don't block submission on validation errors
    }
  }

  // Method to handle date changes and trigger validation
  onDateChange() {
    // Mark both date fields as touched to trigger validation display
    this.clientForm.get('data_emissione')?.markAsTouched();
    this.clientForm.get('data_scadenza')?.markAsTouched();

    // Trigger form validation to update the documentDateInvalid error
    this.clientForm.updateValueAndValidity();
  }

  ngOnInit() {
    // Initialize gender options with translations
    this.genderOptions = [
      { label: this.translocoService.translate('gender-male'), value: '1' },
      { label: this.translocoService.translate('gender-female'), value: '2' }
    ];

    // Load reference data from JSON files
    this.loadAllReferenceDataAsync();

    // Subscribe to language changes to reload country options
    this.translocoService.langChanges$.subscribe(lang => {
      this.languageCode = lang;
      this.loadCountryOptionsAsync();
    });

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

  // Load country options with current language (async version)
  private async loadCountryOptionsAsync(): Promise<void> {
    try {
      const countries = await this.http.get<{ [key: string]: string }>('/assets/data/countries.json').toPromise();
      if (countries) {
        this.countryMappings = countries;
        // Use requestAnimationFrame to avoid blocking UI (if available)
        if (typeof requestAnimationFrame !== 'undefined') {
          requestAnimationFrame(() => {
            this.countryOptions = Object.entries(countries).map(([code, description]) => ({
              label: description,
              value: code
            }));
          });
        } else {
          // Fallback for server-side rendering
          this.countryOptions = Object.entries(countries).map(([code, description]) => ({
            label: description,
            value: code
          }));
        }
      }
    } catch (error) {
      console.error('Error loading countries:', error);
      // Use centralized fallback data
      this.countryOptions = [...FALLBACK_COUNTRY_OPTIONS];
      this.countryMappings = { ...FALLBACK_COUNTRY_MAPPINGS };
    }
  }



  private async loadAllReferenceDataAsync(): Promise<void> {
    try {
      // Load smaller datasets first (countries, document types, province acronyms)
      await Promise.all([
        this.loadCountryOptionsAsync(),
        this.loadDocumentTypesAsync(),
        this.loadProvinceAcronymsAsync()
      ]);

      // Load municipalities data once (this will populate municipalityOptions and luogoEmissioneOptions)
      setTimeout(() => {
        this.loadMunicipalitiesDataAsync();
      }, 100);

      this.dataLoaded = true;
      this.isLoadingData = false;
    } catch (error) {
      console.error('Error loading reference data:', error);
      this.isLoadingData = false;
    }
  }

  // Load document types from JSON mapping (async version)
  private async loadDocumentTypesAsync(): Promise<void> {
    try {
      const documentTypes = await this.http.get<{ [key: string]: string }>('/assets/data/document_types.json').toPromise();
      if (documentTypes) {
        this.documentTypeMappings = documentTypes;
        // Use requestAnimationFrame to avoid blocking UI (if available)
        if (typeof requestAnimationFrame !== 'undefined') {
          requestAnimationFrame(() => {
            this.documentTypeOptions = Object.entries(documentTypes).map(([code, description]) => ({
              label: description,
              value: code
            }));
          });
        } else {
          // Fallback for server-side rendering
          this.documentTypeOptions = Object.entries(documentTypes).map(([code, description]) => ({
            label: description,
            value: code
          }));
        }
      }
    } catch (error) {
      console.error('Error loading document types:', error);
      // Use centralized fallback data
      this.documentTypeOptions = [...FALLBACK_DOCUMENT_TYPE_OPTIONS];
      this.documentTypeMappings = { ...FALLBACK_DOCUMENT_TYPE_MAPPINGS };
    }
  }


  // Load province acronyms from JSON
  private async loadProvinceAcronymsAsync(): Promise<void> {
    try {
      const provinceAcronyms = await this.http.get<{ [key: string]: string }>('/assets/data/province_acronyms.json').toPromise();
      if (provinceAcronyms) {
        // Convert to options format for the select
        this.provinceOptions = Object.entries(provinceAcronyms).map(([acronym, name]) => ({
          label: name,
          value: acronym
        }));
        this.provinceMappings = provinceAcronyms;
      }
    } catch (error) {
      console.error('Error loading province acronyms:', error);
    }
  }

  // Centralized method to load municipalities data and populate both options
  private async loadMunicipalitiesDataAsync(): Promise<void> {
    try {
      const municipalities = await this.http.get<{ [key: string]: string }>('/assets/data/municipalities.json').toPromise();
      if (municipalities) {
        this.municipalityMappings = municipalities;

        // Process municipalities in chunks to avoid blocking UI
        const entries = Object.entries(municipalities);
        const chunkSize = 1000; // Process 1000 entries at a time
        const options: { label: string; value: string }[] = [];

        for (let i = 0; i < entries.length; i += chunkSize) {
          const chunk = entries.slice(i, i + chunkSize);
          const chunkOptions = chunk.map(([code, description]) => ({
            label: description,
            value: code
          }));

          // Add chunk to options array
          options.push(...chunkOptions);

          // Yield control back to the browser to prevent blocking
          if (i + chunkSize < entries.length) {
            await new Promise(resolve => setTimeout(resolve, 0));
          }
        }

        // Sort the options array
        options.sort((a, b) => a.label.localeCompare(b.label));

        // Populate municipality and luogo emissione options (provinces are loaded separately)
        this.municipalityOptions = [...options];
        this.luogoEmissioneOptions = [...options];

        // Set loading states to false
        this.loadingLuogoEmissioneOptions = false;
      }
    } catch (error) {
      console.error('Error loading municipalities data:', error);
      // Use centralized fallback data
      this.municipalityOptions = [...FALLBACK_MUNICIPALITY_OPTIONS];
      this.luogoEmissioneOptions = [...FALLBACK_MUNICIPALITY_OPTIONS];
      this.municipalityMappings = { ...FALLBACK_MUNICIPALITY_MAPPINGS };
      this.luogoEmissioneMappings = { ...FALLBACK_MUNICIPALITY_MAPPINGS };

      // Set loading states to false
      this.loadingLuogoEmissioneOptions = false;
    }
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

    // Set loading state
    this.isSubmitting = true;

    if (this.uploadForm.invalid || this.clientForm.invalid) {
      // Check for specific validation errors
      if (this.clientForm.hasError('documentDateInvalid')) {
        this.messageService.add({
          severity: 'error',
          summary: 'Validation Error',
          detail: this.translocoService.translate('document-expiry-date-error')
        });
      } else {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: this.translocoService.translate('all-fields-required-error') });
      }
      this.isSubmitting = false;
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
      'cap', 'telephone', 'document_type',
      'document_number', 'cf',
      // Portale Alloggi required fields
      'sesso', 'nazionalita', 'email', 'stato_nascita', 'cittadinanza',
      'luogo_emissione', 'data_emissione', 'data_scadenza',
      'autorita_rilascio', 'stato_residenza'
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

    // Add municipality codes for birth and residence
    const birthMunicipalityCode = this.clientForm.get('comune_nascita_code')?.value;
    const residenceMunicipalityCode = this.clientForm.get('comune_residenza_code')?.value;

    if (birthMunicipalityCode) {
      formData.append('comune_nascita', birthMunicipalityCode);
    }
    if (residenceMunicipalityCode) {
      formData.append('comune_residenza', residenceMunicipalityCode);
    }

    // Map municipality names to the expected backend field names
    const birthProvinceCode = this.clientForm.get('provincia_nascita')?.value;
    const residenceProvinceCode = this.clientForm.get('provincia_residenza')?.value;

    // Use province names as municipality names (simplified approach)
    if (birthProvinceCode) {
      const birthProvinceName = this.provinceMappings[birthProvinceCode];
      if (birthProvinceName) {
        formData.append('comune_nascita', birthProvinceName);
      }
    }
    if (residenceProvinceCode) {
      const residenceProvinceName = this.provinceMappings[residenceProvinceCode];
      if (residenceProvinceName) {
        formData.append('comune_residenza', residenceProvinceName);
      }
    }

    // Send province acronyms directly (no conversion needed)
    if (birthProvinceCode) {
      formData.append('provincia_nascita', birthProvinceCode);
    }
    if (residenceProvinceCode) {
      formData.append('provincia_residenza', residenceProvinceCode);
    }

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
        this.isSubmitting = false;
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
        this.isSubmitting = false;
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

  getImagePreview(type: 'frontimage' | 'backimage' | 'selfie'): string | null {
    const file = this.uploadForm.get(type)?.value;
    if (file && file.objectURL) {
      return file.objectURL;
    }
    return null;
  }


  // Helper method to get country display name by code
  getCountryDisplayName(code: string): string {
    return this.countryMappings[code] || code;
  }

  // Helper method to get municipality display name by code
  getMunicipalityDisplayName(code: string): string {
    return this.municipalityMappings[code] || code;
  }

  // Helper method to get document type display name by code
  getDocumentTypeDisplayName(code: string): string {
    return this.documentTypeMappings[code] || code;
  }


  // Helper method to get birth province name for display
  getBirthProvinceName(): string {
    const code = this.clientForm.get('provincia_nascita')?.value;
    if (!code) return '';
    // Get province name from acronym
    return this.provinceMappings[code] || code;
  }

  // Helper method to get residence province name for display
  getResidenceProvinceName(): string {
    const code = this.clientForm.get('provincia_residenza')?.value;
    if (!code) return '';
    // Get province name from acronym
    return this.provinceMappings[code] || code;
  }


  // Helper method to get luogo emissione name for display
  getLuogoEmissioneName(): string {
    const code = this.clientForm.get('luogo_emissione')?.value;
    return code ? this.getMunicipalityDisplayName(code) || code : '';
  }






}
