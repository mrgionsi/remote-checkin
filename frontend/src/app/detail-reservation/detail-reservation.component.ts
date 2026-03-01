import { Component, OnInit } from '@angular/core';
import { ReservationService } from '../services/reservation.service';
import { ToastModule } from 'primeng/toast';
import { MessageService, ConfirmationService } from 'primeng/api';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { TableModule } from 'primeng/table';
import { CardModule } from 'primeng/card';
import { ClientReservationService } from '../services/client-reservation.service';
import { DialogService } from 'primeng/dynamicdialog';
import { environment } from '../../environments/environments';
import { PersonDetailDialogComponent } from '../person-detail-dialog/person-detail-dialog.component';
import { ButtonModule } from 'primeng/button';
import { Subscription } from 'rxjs';
import { SelectModule } from 'primeng/select';

import { AbstractControl, FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { DocumentTypeLabelPipe } from "../pipes/document-type-label.pipe";
import { DatePickerModule } from 'primeng/datepicker';
import { RoomService } from '../services/room.service';
import {
  FALLBACK_MUNICIPALITY_MAPPINGS,
  FALLBACK_DOCUMENT_TYPE_MAPPINGS
} from '../shared/constants/fallback-data';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DialogModule } from 'primeng/dialog';
import { HttpClient } from '@angular/common/http';
import { TranslocoPipe, TranslocoService } from '@jsverse/transloco';
import { PortaleAlloggiService } from '../services/portale-alloggi.service';

@Component({
  selector: 'app-detail-reservation',
  imports: [ToastModule, TranslocoPipe, CommonModule, TableModule, ConfirmDialogModule, CardModule, ButtonModule, FormsModule, SelectModule, DatePickerModule, ReactiveFormsModule, DialogModule],
  templateUrl: './detail-reservation.component.html',
  styleUrl: './detail-reservation.component.scss',
  providers: [MessageService, DialogService, ConfirmationService]

})
export class DetailReservationComponent implements OnInit {
  private subscriptions: Subscription[] = [];
  people: any[] = [];  // Initialize as an empty array
  reservation_details: any = {}; // Initialize as an empty object
  noClientDataYet = false;
  reservationId: any;
  reservation_status: any;
  loading = true;
  saving = false;
  statusOptions = [
    { label: 'status-approved', value: 'Approved', icon: 'pi pi-check-circle' },
    { label: 'status-declined', value: 'Declined', icon: 'pi pi-times-circle' },
    { label: 'status-sent-back-to-customer', value: 'Sent back to customer', icon: 'pi pi-arrow-left' },
    { label: 'status-pending', value: 'Pending', icon: 'pi pi-clock' },
  ];

  roomList: any;
  editMode = false;
  form: FormGroup;

  // Portale Alloggi modal
  showPortaleAlloggiModal = false;
  sendingToPortaleAlloggi = false;

  // Portale Alloggi submission status
  portaleAlloggiSent = false;
  portaleAlloggiSentAt: string | null = null;
  portaleAlloggiResponse: string | null = null;

  // Development mode
  isDevelopment = environment.development;

  // Mapping data for display
  countryMappings: { [key: string]: string } = {};
  municipalityMappings: { [key: string]: string } = {};
  documentTypeMappings: { [key: string]: string } = {};


  constructor(
    private messageService: MessageService,
    private route: ActivatedRoute,
    private client_reservationService: ClientReservationService,
    private readonly dialogService: DialogService,
    private readonly fb: FormBuilder,
    private readonly reservation_service: ReservationService,
    private readonly roomService: RoomService,
    private readonly confirmationService: ConfirmationService,
    private readonly router: Router,
    private readonly translocoService: TranslocoService,
    private readonly portaleAlloggiService: PortaleAlloggiService,
    private http: HttpClient
  ) {
    this.form = this.fb.group({
      id_reference: ['', Validators.required],
      room: [''],
      start_date: ['', Validators.required],
      end_date: ['', Validators.required],
      name_reference: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      telephone: [''],
      status: [''],
      number_of_people: [1, [Validators.required, Validators.min(1)]],
    }, { validators: this.dateRangeValidator });
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  dateRangeValidator(group: AbstractControl): { [key: string]: any } | null {
    const start = group.get('start_date')?.value;
    const end = group.get('end_date')?.value;

    if (start && end && new Date(start) > new Date(end)) {
      return { endDateBeforeStartDate: true };
    }
    return null;
  }

  ngOnInit(): void {
    // Load reference data for display mappings
    this.loadReferenceData();

    var reservationId: number;
    this.route.params.subscribe(params => {
      reservationId = params['id_reservation'];
      //console.log(reservationId);
      this.reservationId = reservationId;
      this.reservation_service.getAdminReservationById(reservationId).subscribe({
        next: (resp) => {
          this.reservation_details = resp;
          console.log("Resp", resp);
          if (!this.isReservationInSelectedStructure(resp)) {
            return;
          }
          this.reservation_status = this.statusOptions.find(option => option.value === resp.status);
          this.loading = false;

          // Load Portale Alloggi submission status
          this.loadPortaleAlloggiStatus();

          this.client_reservationService.getClientByReservationId(this.reservation_details.id).subscribe({
            next: (r) => {
              if (!Array.isArray(r) || r.length === 0) {
                this.people = [];
                this.noClientDataYet = true;
                return;
              }

              this.noClientDataYet = false;
              this.people = r;
              this.people.forEach(person => {
                const photoSub = this.client_reservationService.getUserPhoto(this.reservation_details.id_reference, person.name, person.surname, person.cf).subscribe({
                  next: (person_photo: any) => {
                    //console.log(person_photo)

                    person.images = {};
                    if (person_photo.back_image) {
                      this.loadPersonImage(person, 'back', environment.apiBaseUrl + person_photo.back_image);
                    } else {
                      person.images.back = null;
                    }
                    if (person_photo.front_image) {
                      this.loadPersonImage(person, 'front', environment.apiBaseUrl + person_photo.front_image);
                    } else {
                      person.images.front = null;
                    }
                    if (person_photo.selfie) {
                      this.loadPersonImage(person, 'selfie', environment.apiBaseUrl + person_photo.selfie);
                    } else {
                      person.images.selfie = null;
                    }
                    person.hasMissingImages = !person_photo.back_image || !person_photo.front_image || !person_photo.selfie;

                    //console.log(person)
                  },
                  error: (error: any) => {
                    console.error('Error fetching client photo:', error);
                    this.messageService.add({
                      severity: 'warn',
                      summary: 'Photo Loading Error',
                      detail: `Error loading photos for ${person.name} ${person.surname}. Some images may not be available.`
                    });
                    person.hasMissingImages = true; // Assume missing if API request fails
                    // Initialize empty images object to prevent undefined errors
                    person.images = { front: null, back: null, selfie: null };
                  }
                })
                this.subscriptions.push(photoSub);
              })

            },
            error: (err: any) => {
              const noDataYet = err?.status === 404 && String(err?.error?.error || '').includes('No clients found');
              if (noDataYet) {
                this.people = [];
                this.noClientDataYet = true;
                return;
              }

              this.noClientDataYet = false;
              this.messageService.add({
                severity: 'error',
                summary: this.translocoService.translate('error'),
                detail: this.translocoService.translate('reservation-client-details-fetch-error')
              });
            },
            complete: () => {

            }
          })
        },
        error: (error) => {
          console.log(error);
          switch (error.status) {
            case 404:
              this.messageService.add({ severity: 'warn', summary: 'Error', detail: 'Reservation not found.' });
              break;
            default:
              this.messageService.add({ severity: 'warn', summary: 'Error', detail: 'Error fetching reservation details.' });
          }

        }
      })

      const selectedStructureId = Number(localStorage.getItem('selected_structure_id') || 0);
      this.roomService.getRooms(selectedStructureId || null).subscribe({
        next: (value) => {
          console.log(value)
          this.roomList = value;
          // If we're already in edit mode, update the room selection
          if (this.editMode) {
            this.updateRoomSelection();
          }
        },
        error: (msg) => {
          console.error("Failed to fetch rooms")
          this.messageService.add({ severity: 'warn', summary: 'Failed', detail: 'Unable to load room data. You can continue, but room selection may be unavailable.' });
        }
      })
    })

    // Add validation for number of people against room capacity
    this.form.get('room')?.valueChanges.subscribe(() => {
      this.validateNumberOfPeople();
    });

    this.form.get('number_of_people')?.valueChanges.subscribe(() => {
      this.validateNumberOfPeople();
    });

  }

  private isReservationInSelectedStructure(reservation: any): boolean {
    const selectedStructureId = Number(localStorage.getItem('selected_structure_id') || 0);
    const reservationStructureId = reservation?.room?.id_structure;

    if (!selectedStructureId || !reservationStructureId) {
      return true;
    }

    if (selectedStructureId !== reservationStructureId) {
      this.messageService.add({
        severity: 'warn',
        summary: this.translocoService.translate('access-restricted'),
        detail: this.translocoService.translate('reservation-structure-mismatch')
      });
      this.router.navigate(['/admin/dashboard']);
      return false;
    }

    return true;
  }

  // Method to validate number of people against room capacity
  validateNumberOfPeople(): void {
    const room = this.form.get('room')?.value;
    const numberOfPeople = this.form.get('number_of_people')?.value;

    if (room && numberOfPeople) {
      const selectedRoom = this.roomList?.find((r: any) => r.id === room.id);
      if (selectedRoom && numberOfPeople > selectedRoom.capacity) {
        this.form.get('number_of_people')?.setErrors({
          'exceedsCapacity': true,
          'maxCapacity': selectedRoom.capacity
        });
      } else {
        const currentErrors = this.form.get('number_of_people')?.errors;
        if (currentErrors) {
          delete currentErrors['exceedsCapacity'];
          delete currentErrors['maxCapacity'];
          this.form.get('number_of_people')?.setErrors(
            Object.keys(currentErrors).length > 0 ? currentErrors : null
          );
        }
      }
    }
  }

  editReservation() {

    this.editMode = true;

    // Convert dates to proper Date objects for the datepicker
    const startDate = this.reservation_details.start_date ? new Date(this.reservation_details.start_date) : null;
    const endDate = this.reservation_details.end_date ? new Date(this.reservation_details.end_date) : null;

    console.log('Date conversion:', {
      originalStartDate: this.reservation_details.start_date,
      convertedStartDate: startDate,
      originalEndDate: this.reservation_details.end_date,
      convertedEndDate: endDate
    });

    this.form.patchValue({
      id_reference: this.reservation_details.id_reference,
      start_date: startDate,
      end_date: endDate,
      name_reference: this.reservation_details.name_reference,
      email: this.reservation_details.email,
      telephone: this.reservation_details.telephone,
      status: this.reservation_details.status,
      number_of_people: this.reservation_details.number_of_people || 1,
    });

    // Update room selection (will work if roomList is already loaded)
    this.updateRoomSelection();

  }

  updateRoomSelection(): void {
    if (this.reservation_details.room && this.roomList) {
      console.log('Updating room selection:', {
        reservationRoom: this.reservation_details.room,
        roomList: this.roomList
      });
      const selectedRoom = this.roomList.find((room: any) => room.id === this.reservation_details.room.id);
      console.log('Found selected room:', selectedRoom);
      if (selectedRoom) {
        this.form.patchValue({ room: selectedRoom });
        console.log('Room selection updated in form');
      } else {
        console.log('Room not found in roomList, using reservation room object');
        // Fallback: use the reservation room object directly
        this.form.patchValue({ room: this.reservation_details.room });
      }
    } else {
      console.log('Cannot update room selection:', {
        hasReservationRoom: !!this.reservation_details.room,
        hasRoomList: !!this.roomList
      });
      // If roomList is not loaded yet, use the reservation room object as fallback
      if (this.reservation_details.room) {
        this.form.patchValue({ room: this.reservation_details.room });
        console.log('Using reservation room as fallback');
      }
    }
  }

  saveReservation() {
    if (this.form.valid) {
      const reservationId = this.reservation_details.id;
      this.saving = true;
      // Don't set editMode = false here - let it be set after successful save

      // Prepare update data with proper room structure
      const updateData = { ...this.form.value };
      updateData.id = reservationId;

      // Handle room object - ensure it has the correct structure for backend
      if (updateData.room && typeof updateData.room === 'object' && updateData.room.id) {
        updateData.room = { id: updateData.room.id };
      }

      // Create Date object from start_date
      const endDate = new Date(this.form.value.end_date);
      // Set time to 03:00:00
      endDate.setHours(3, 0, 0, 0);
      // Convert to the correct format (GMT)
      updateData.end_date = endDate.toUTCString();

      const startDate = new Date(this.form.value.start_date);
      // Set time to 03:00:00
      startDate.setHours(3, 0, 0, 0);
      updateData.start_date = startDate.toUTCString();

      // Check if status has changed and update it separately
      const statusChanged = this.reservation_status &&
        this.reservation_status.value !== this.reservation_details.status;

      // Persist data to backend
      console.log('Updating reservation with data:', updateData);
      this.reservation_service.updateReservation(updateData, reservationId).subscribe({
        next: () => {
          // If status has changed, update it separately
          if (statusChanged) {
            this.reservation_service.updateReservationStatus(reservationId, this.reservation_status.value).subscribe({
              next: () => {
                this.saving = false;
                this.editMode = false; // Exit edit mode on success
                this.refreshReservationData(reservationId);
              },
              error: (error: any) => {
                this.saving = false;
                this.editMode = true; // Re-enable edit mode on error
                this.messageService.add({
                  severity: 'error',
                  summary: 'Error',
                  detail: 'Failed to update reservation status.'
                });
              }
            });
          } else {
            this.saving = false;
            this.editMode = false; // Exit edit mode on success
            this.refreshReservationData(reservationId);
          }
        },
        error: (error: any) => {
          this.saving = false;
          this.editMode = true; // Re-enable edit mode on error
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to update the reservation.'
          });
          console.log(error)
        }
      });
    } else {
      // Add feedback for invalid form
      this.messageService.add({
        severity: 'error',
        summary: 'Validation Error',
        detail: 'Please correct the highlighted fields before saving.'
      });
      // Mark all form controls as touched to trigger validation styling
      Object.keys(this.form.controls).forEach(key => {
        const control = this.form.get(key);
        control?.markAsTouched();
      });
    }
  }



  cancelEdit() {
    this.editMode = false;
    this.form.reset();
  }



  formatDateOnly(date: Date): string {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0'); // Months are 0-based
    const day = date.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  openDetails(person: any) {
    this.dialogService.open(PersonDetailDialogComponent, {
      data: { person },
      header: 'Person Details',
      width: '95vw', // Adjust width (80% of the viewport width)
      height: '95vh', // Adjust height (70% of the viewport height)
      closable: true,
      modal: true,
      contentStyle: { 'max-height': '99vh', 'overflow-y': 'auto' }, // Allow content to scroll if it overflows
    });
  }

  confirmDeleteReservation() {
    this.confirmationService.confirm({
      message: 'Are you sure you want to delete this reservation?',
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.removeReservation(); // actually call API
      }
    });
  }

  removeReservation() {
    const reservationId = this.reservation_details.id;
    this.reservation_service.deleteReservation(reservationId).subscribe({
      next: () => {
        this.messageService.add({ severity: 'success', summary: 'Deleted', detail: 'Reservation deleted' });
        setTimeout(() => {
          this.router.navigate(['/admin/dashboard']);
        }, 1000);
      },
      error: (err) => {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Deletion failed' });
        console.error('Delete error', err);
      }
    });
  }
  onStatusChange(newStatus: { value: string, label: string, icon: string }): void {
    // Just update the local status - the actual update will happen when saving
    this.reservation_status = newStatus;
    console.log('Status changed locally to:', newStatus);
  }

  private refreshReservationData(reservationId: number): void {
    // Refresh reservation details from backend to ensure we have the latest data
    this.reservation_service.getAdminReservationById(reservationId).subscribe({
      next: (updatedReservation) => {
        this.reservation_details = updatedReservation;
        this.reservation_status = this.statusOptions.find(option => option.value === updatedReservation.status);
        console.log('Refreshed reservation_details from backend:', this.reservation_details);

        this.messageService.add({
          severity: 'success',
          summary: this.translocoService.translate('updated'),
          detail: this.translocoService.translate('reservation-updated-success')
        });
      },
      error: (error) => {
        console.error('Error refreshing reservation details:', error);
        // Fallback: update local data manually
        this.reservation_details = { ...this.reservation_details, ...this.form.value };

        // If room was changed, update the room object in reservation_details
        if (this.form.value.room && this.roomList) {
          const updatedRoom = this.roomList.find((room: any) => room.id === this.form.value.room.id);
          if (updatedRoom) {
            this.reservation_details.room = updatedRoom;
          }
        }

        // Show error toast for refresh failure
        this.messageService.add({
          severity: 'warn',
          summary: 'Partial Update',
          detail: 'Reservation was updated locally but failed to refresh from server. Data may not be fully synchronized.'
        });
      }
    });
  }

  // Funzione per scaricare l'immagine con autenticazione
  loadPersonImage(person: any, type: 'front' | 'back' | 'selfie', url: string) {
    const token = localStorage.getItem('admin_token');
    this.http.get(url, {
      responseType: 'blob',
      headers: { Authorization: `Bearer ${token}` }
    }).subscribe({
      next: (blob) => {
        person.images[type] = URL.createObjectURL(blob);
      },
      error: (error) => {
        console.error(`Error loading ${type} image for ${person.name}:`, error);
        person.images[type] = null;
      }
    });
  }

  /**
   * Generate a CSS class name for status values.
   * Converts the status value to lowercase, trims whitespace, and replaces all whitespace with hyphens.
   * 
   * @param value - The status value to convert to a CSS class
   * @returns A CSS class string in the format 'status-{normalized-value}'
   */
  statusClass(value: string): string {
    if (!value) {
      return 'status-pending';
    }
    const normalized = value.toLowerCase().trim().replace(/\s+/g, '-');
    return `status-${normalized}`;
  }

  // Portale Alloggi modal methods
  openPortaleAlloggiModal(): void {
    if (this.people.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Warning',
        detail: this.translocoService.translate('no-guests-to-send')
      });
      return;
    }
    this.showPortaleAlloggiModal = true;
  }

  closePortaleAlloggiModal(): void {
    this.showPortaleAlloggiModal = false;
  }

  sendToPortaleAlloggi(): void {
    this.sendingToPortaleAlloggi = true;

    this.portaleAlloggiService.sendReservationDataTest(this.reservationId).subscribe({
      next: (response) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: this.translocoService.translate('data-sent-success')
        });
        this.sendingToPortaleAlloggi = false;
        this.closePortaleAlloggiModal();

        // Update local status after successful submission
        this.portaleAlloggiSent = true;
        this.portaleAlloggiSentAt = new Date().toISOString();
        this.portaleAlloggiResponse = response.result || '';
      },
      error: (error) => {
        console.error('Error sending to Portale Alloggi:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: this.resolvePortaleErrorMessage(error)
        });
        this.sendingToPortaleAlloggi = false;
      }
    });
  }

  // Send to Portale Alloggi (TEST MODE)
  sendToPortaleAlloggiTest(): void {
    this.sendingToPortaleAlloggi = true;

    this.portaleAlloggiService.sendReservationDataTest(this.reservationId).subscribe({
      next: (response) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: this.translocoService.translate('data-sent-success-test')
        });
        this.sendingToPortaleAlloggi = false;
        this.closePortaleAlloggiModal();

        // DO NOT update submission status for test mode
        // Test submissions should not disable buttons
      },
      error: (error) => {
        console.error('Error sending to Portale Alloggi (TEST):', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: this.resolvePortaleErrorMessage(error)
        });
        this.sendingToPortaleAlloggi = false;
      }
    });
  }

  // Send to Portale Alloggi (REAL PRODUCTION)
  sendToPortaleAlloggiReal(): void {
    this.sendingToPortaleAlloggi = true;

    this.portaleAlloggiService.sendReservationDataReal(this.reservationId).subscribe({
      next: (response) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: this.translocoService.translate('data-sent-success-real')
        });
        this.sendingToPortaleAlloggi = false;
        this.closePortaleAlloggiModal();

        // Update local status after successful submission
        this.portaleAlloggiSent = true;
        this.portaleAlloggiSentAt = new Date().toISOString();
        this.portaleAlloggiResponse = response.result || '';
      },
      error: (error) => {
        console.error('Error sending to Portale Alloggi (REAL):', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: this.resolvePortaleErrorMessage(error)
        });
        this.sendingToPortaleAlloggi = false;
      }
    });
  }

  private resolvePortaleErrorMessage(error: any): string {
    const backendError = error?.error?.error;
    if (backendError === 'Portale Alloggi credentials not configured') {
      return this.translocoService.translate('portale-alloggi-not-configured');
    }
    return backendError || this.translocoService.translate('data-send-failed');
  }

  // Load Portale Alloggi submission status
  loadPortaleAlloggiStatus(): void {
    if (!this.reservationId) return;

    this.portaleAlloggiService.getSubmissionStatus(this.reservationId).subscribe({
      next: (response) => {
        this.portaleAlloggiSent = response.portale_alloggi_sent;
        this.portaleAlloggiSentAt = response.portale_alloggi_sent_at;
        this.portaleAlloggiResponse = response.portale_alloggi_response;
      },
      error: (error) => {
        console.error('Error loading Portale Alloggi status:', error);
      }
    });
  }

  // Load reference data from JSON files
  private loadReferenceData() {
    Promise.all([
      this.loadCountries(),
      this.loadMunicipalities(),
      this.loadDocumentTypes()
    ]).catch(error => {
      console.error('Error loading reference data:', error);
      this.initializeFallbackData();
    });
  }

  private async loadCountries(): Promise<void> {
    try {
      const countries = await this.http.get<{ [key: string]: string }>('/assets/data/countries.json').toPromise();
      if (countries) {
        this.countryMappings = countries;
      }
    } catch (error) {
      console.error('Error loading countries:', error);
      this.initializeFallbackCountries();
    }
  }

  private async loadMunicipalities(): Promise<void> {
    try {
      const municipalities = await this.http.get<{ [key: string]: string }>('/assets/data/municipalities.json').toPromise();
      if (municipalities) {
        this.municipalityMappings = municipalities;
      }
    } catch (error) {
      console.error('Error loading municipalities:', error);
      this.initializeFallbackMunicipalities();
    }
  }

  private async loadDocumentTypes(): Promise<void> {
    try {
      const documentTypes = await this.http.get<{ [key: string]: string }>('/assets/data/document_types.json').toPromise();
      if (documentTypes) {
        this.documentTypeMappings = documentTypes;
      }
    } catch (error) {
      console.error('Error loading document types:', error);
      this.initializeFallbackDocumentTypes();
    }
  }

  private initializeFallbackData() {
    this.initializeFallbackCountries();
    this.initializeFallbackMunicipalities();
    this.initializeFallbackDocumentTypes();
  }

  private initializeFallbackCountries() {
    this.countryMappings = {
      '100000100': 'ITALIA',
      '100000536': 'STATI UNITI D\'AMERICA',
      '100000219': 'REGNO UNITO',
      '100000215': 'FRANCIA'
    };
  }

  private initializeFallbackMunicipalities() {
    this.municipalityMappings = {
      '058091': 'ROMA',
      '015146': 'MILANO',
      '063049': 'NAPOLI',
      '001272': 'TORINO'
    };
  }

  private initializeFallbackDocumentTypes() {
    this.documentTypeMappings = {
      'IDENT': 'CARTA DI IDENTITA\'',
      'PASOR': 'PASSAPORTO ORDINARIO',
      'PATEN': 'PATENTE DI GUIDA',
      'IDELE': 'CARTA IDENTITA\' ELETTRONICA'
    };
  }

  // Helper method to get country display name by code
  getCountryDisplayName(code: string): string {
    return this.countryMappings[code] || code || '-';
  }

  // Helper method to get municipality display name by code
  getMunicipalityDisplayName(code: string): string {
    return this.municipalityMappings[code] || code || '-';
  }

  // Helper method to get document type display name by code
  getDocumentTypeDisplayName(code: string): string {
    return this.documentTypeMappings[code] || code || '-';
  }

  // Helper method to determine guest type for a specific person
  getGuestTypeForPerson(person: any, personIndex: number): string {
    const totalGuests = this.people.length;

    if (totalGuests === 1) {
      return this.translocoService.translate('ospite-singolo');
    } else if (totalGuests > 1) {
      // Check if this is a family reservation (same surnames)
      const surnames = this.people.map(p => p.surname?.toUpperCase().trim()).filter(s => s);
      const uniqueSurnames = [...new Set(surnames)];

      const isFamily = uniqueSurnames.length === 1 || uniqueSurnames.length <= totalGuests / 2;

      if (isFamily) {
        if (personIndex === 0) {
          return this.translocoService.translate('capo-famiglia');
        } else {
          return this.translocoService.translate('familiare');
        }
      } else {
        if (personIndex === 0) {
          return this.translocoService.translate('capo-gruppo');
        } else {
          return this.translocoService.translate('membro-gruppo');
        }
      }
    }

    return this.translocoService.translate('ospite-singolo');
  }
}
