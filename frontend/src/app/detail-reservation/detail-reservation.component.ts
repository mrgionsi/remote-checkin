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
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { HttpClient } from '@angular/common/http';
import { TranslocoPipe } from '@jsverse/transloco';

@Component({
  selector: 'app-detail-reservation',
  imports: [ToastModule, TranslocoPipe, CommonModule, TableModule, ConfirmDialogModule, CardModule, ButtonModule, FormsModule, SelectModule, DatePickerModule, ReactiveFormsModule, DocumentTypeLabelPipe],
  templateUrl: './detail-reservation.component.html',
  styleUrl: './detail-reservation.component.scss',
  providers: [MessageService, DialogService, ConfirmationService]

})
export class DetailReservationComponent implements OnInit {
  private subscriptions: Subscription[] = [];
  people: any[] = [];  // Initialize as an empty array
  reservation_details: any = {}; // Initialize as an empty object
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
    var reservationId: number;
    this.route.params.subscribe(params => {
      reservationId = params['id_reservation'];
      //console.log(reservationId);
      this.reservationId = reservationId;
      this.reservation_service.getAdminReservationById(reservationId).subscribe({
        next: (resp) => {
          this.reservation_details = resp;
          console.log("Resp", resp);
          this.reservation_status = this.statusOptions.find(option => option.value === resp.status);
          this.loading = false;

          this.client_reservationService.getClientByReservationId(this.reservation_details.id).subscribe({
            next: (r) => {
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
            error: (err) => {
              this.messageService.add({ severity: 'warn', summary: 'Error', detail: 'Error fetching client details.' });
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

      this.roomService.getRooms().subscribe({
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
          summary: 'Updated',
          detail: 'Reservation has been successfully updated.'
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

        this.messageService.add({
          severity: 'success',
          summary: 'Updated',
          detail: 'Reservation has been successfully updated.'
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
}
