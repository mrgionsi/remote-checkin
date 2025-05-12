import { Component, OnInit } from '@angular/core';
import { ReservationService } from '../services/reservation.service';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { ActivatedRoute } from '@angular/router';
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
import { DateShortPipe } from "../pipes/date-short.pipe";
import { RoomService } from '../services/room.service';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ConfirmationService } from 'primeng/api';
import { Router } from '@angular/router';

@Component({
  selector: 'app-detail-reservation',
  imports: [ToastModule, CommonModule, TableModule, ConfirmDialogModule, CardModule, ButtonModule, FormsModule, SelectModule, DocumentTypeLabelPipe, DatePickerModule, ReactiveFormsModule, DateShortPipe],
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
  statusOptions = [
    { label: 'Approved', value: 'Approved', icon: 'pi pi-check-circle' },
    { label: 'Declined', value: 'Declined', icon: 'pi pi-times-circle' },
    { label: 'Sent back to customer', value: 'Sent back to customer', icon: 'pi pi-arrow-left' },
    { label: 'Pending', value: 'Pending', icon: 'pi pi-clock' },

  ];

  roomList: any;
  editMode = false;
  form: FormGroup;


  constructor(private reservationService: ReservationService,
    private messageService: MessageService,
    private route: ActivatedRoute,
    private client_reservationService: ClientReservationService,
    private dialogService: DialogService,
    private fb: FormBuilder,
    private reservation_service: ReservationService,
    private roomService: RoomService,
    private confirmationService: ConfirmationService,
    private router: Router
  ) {
    this.form = this.fb.group({
      id_reference: ['', Validators.required],
      room: [''],
      start_date: ['', Validators.required],
      end_date: ['', Validators.required],
      name_reference: ['', Validators.required],
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
    const _ = this;
    this.route.params.subscribe(params => {
      reservationId = params['id_reservation']; // Default to 'en' if missing
      //console.log(reservationId);
      this.reservationId = reservationId;
      this.reservationService.getReservationById(reservationId).subscribe({
        next: (resp) => {
          this.reservation_details = resp;
          console.log("Resp", resp);
          this.reservation_status = _.statusOptions.find(option => option.value === resp.status)

          this.client_reservationService.getClientByReservationId(this.reservation_details.id).subscribe({
            next: (r) => {
              this.people = r;
              this.people.forEach(person => {
                const photoSub = this.client_reservationService.getUserPhoto(reservationId, person.name, person.surname, person.cf).subscribe({
                  next: (person_photo: any) => {
                    //console.log(person_photo)
                    person.images = [];
                    person.images.back = person_photo.back_image ? environment.apiBaseUrl + person_photo?.back_image : null;
                    person.images.front = person_photo.front_image ? environment.apiBaseUrl + person_photo?.front_image : null;
                    person.images.selfie = person_photo.selfie ? environment.apiBaseUrl + person_photo?.selfie : null;
                    person.hasMissingImages = !person_photo.back_image || !person_photo.front_image || !person_photo.selfie;

                    //console.log(person)
                  },
                  error: (error: any) => {
                    this.messageService.add({ severity: 'warn', summary: 'Error', detail: 'Error fetching client photo for ' + person.name + ' ' + person.surname + ', please try again.' });
                    person.hasMissingImages = true; // Assume missing if API request fails

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
    this.form.patchValue({
      id_reference: this.reservation_details.id_reference,
      room: this.reservation_details['room'],
      start_date: this.reservation_details.start_date,
      end_date: this.reservation_details.end_date,
      name_reference: this.reservation_details.name_reference,
      status: this.reservation_details.status,
    });

  }

  saveReservation() {
    if (this.form.valid) {
      const reservationId = this.reservation_details.id;
      this.editMode = false;
      this.reservation_details = { ...this.form.value };
      // Create Date object from start_date
      this.reservation_details.id = reservationId;
      const endDate = new Date(this.form.value.end_date);

      // Set time to 03:00:00
      endDate.setHours(3, 0, 0, 0);

      // Convert to the correct format (GMT)
      this.reservation_details.end_date = endDate.toUTCString();
      const startDate = new Date(this.form.value.start_date);

      // Set time to 03:00:00
      startDate.setHours(3, 0, 0, 0);
      this.reservation_details.start_date = startDate.toUTCString();

      // Optionally persist data to backend
      console.log(this.reservation_details)
      this.reservation_service.updateReservation(this.reservation_details, reservationId).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Updated',
            detail: 'Reservation has been successfully updated.'
          });
          // Redirect to reservations list or dashboard
        },
        error: (error: any) => {
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
    this.reservationService.deleteReservation(reservationId).subscribe({
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
  onStatusChange(newStatus: any) {
    if (!this.reservation_details?.id) return;
    console.log(newStatus)
    this.reservationService.updateReservationStatus(this.reservation_details.id, newStatus.value).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Status Updated',
          detail: `Reservation status updated to ${newStatus.value}.`
        });
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Update Failed',
          detail: 'Could not update reservation status. Please try again.'
        });
        // Optionally revert the value here
      }
    });
  }


}
