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
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { DocumentTypeLabelPipe } from "../pipes/document-type-label.pipe";
import { DatePickerModule } from 'primeng/datepicker';
import { DateShortPipe } from "../pipes/date-short.pipe";

@Component({
  selector: 'app-detail-reservation',
  imports: [ToastModule, CommonModule, TableModule, CardModule, ButtonModule, FormsModule, SelectModule, DocumentTypeLabelPipe, DatePickerModule, ReactiveFormsModule, DateShortPipe],
  templateUrl: './detail-reservation.component.html',
  styleUrl: './detail-reservation.component.scss',
  providers: [MessageService, DialogService]

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
  editMode = false;
  form: FormGroup;


  constructor(private reservationService: ReservationService,
    private messageService: MessageService,
    private route: ActivatedRoute,
    private client_reservationService: ClientReservationService,
    private dialogService: DialogService,
    private fb: FormBuilder,
  ) {
    this.form = this.fb.group({
      id_reference: [this.reservation_details?.id_reference, Validators.required],
      room_name: [this.reservation_details?.room?.name],
      start_date: [this.reservation_details?.start_date, Validators.required],
      end_date: [this.reservation_details?.end_date, Validators.required],
      name_reference: [this.reservation_details?.name_reference, Validators.required],
      status: [this.reservation_details?.status],
    });
  }
  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }


  ngOnInit(): void {
    var reservationId: number;
    var _ = this;
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
                this.client_reservationService.getUserPhoto(reservationId, person.name, person.surname, person.cf).subscribe({
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
    })

  }



  editReservation() {
    this.editMode = true;
    this.form.patchValue({
      id_reference: this.reservation_details.id_reference,
      room_name: this.reservation_details['room']['name'] || '',
      start_date: this.reservation_details.start_date,
      end_date: this.reservation_details.end_date,
      name_reference: this.reservation_details.name_reference,
      status: this.reservation_details.status,
    });

  }

  saveReservation() {
    if (this.form.valid) {
      this.editMode = false;
      this.form.get('start_date')?.setValue(this.reservation_details.start_date instanceof Date ? this.reservation_details.start_date.toISOString().split('T')[0] : this.reservation_details.start_date)

      this.reservation_details = { ...this.form.value };
      // Optionally persist data to backend
      console.log(this.reservation_details)

    }
  }

  cancelEdit() {
    this.editMode = false;
  }

  removeReservation() {
    if (confirm('Are you sure you want to remove this reservation?')) {
      this.reservationService.deleteReservation(this.reservationId).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Deleted',
            detail: 'Reservation has been successfully removed.'
          });
          // Redirect to reservations list or dashboard
        },
        error: (error: any) => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to remove the reservation.'
          });
        }
      });
    }
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
  /* 
    approveReservation(reservation: any) {
      this.reservationService.updateReservationStatus(reservation.id, "Approved").subscribe({
        next: (response) => {
          console.log('Status updated successfully:', response);
          // Display success message using PrimeNG MessageService
          this.refreshStatus("Approved");
          this.messageService.add({
            severity: 'success',
            summary: 'Reservation Approved',
            detail: `Reservation ${response.reservation.id_reference} has been approved.`
          });
        },
        error: (error) => {
          console.error('Error updating status:', error);
          // Display error message if something goes wrong
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: `Failed to update the reservation status. Please try again.`
          });
        }
      });
  
    } */
  /* 
    declineReservation(reservation: any) {
      this.reservationService.updateReservationStatus(reservation.id, "Declined").subscribe({
        next: (response) => {
          console.log('Status updated successfully:', response);
          // Display success message using PrimeNG MessageService
          this.messageService.add({ severity: 'error', summary: 'Reservation Declined', detail: `Reservation ${reservation.id_reference} has been declined.` });
          this.refreshStatus("Declined");
  
        },
        error: (error) => {
          console.error('Error updating status:', error);
          // Display error message if something goes wrong
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: `Failed to update the reservation status. Please try again.`
          });
        }
      });
      // Call API to decline reservation
    } */

  /*   sendBackToClient(reservation: any) {
      this.reservationService.updateReservationStatus(reservation.id, "Sent back to customer").subscribe({
        next: (response) => {
          console.log('Status updated successfully:', response);
          // Display success message using PrimeNG MessageService
          this.messageService.add({ severity: 'warn', summary: 'Reservation sent back to customer', detail: `Reservation ${reservation.id_reference} has been sent back to the customer.` });
          this.refreshStatus("Sent back to customer");
  
        },
        error: (error) => {
          console.error('Error updating status:', error);
          // Display error message if something goes wrong
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: `Failed to update the reservation status. Please try again.`
          });
        }
      });
      // Call API to decline reservation
    } */

  /*   // Get the class for status to apply background color or styles
    getStatusClass(status: string): string {
      switch (status) {
        case 'Approved':
          return 'status-approved';
        case 'Pending':
          return 'status-pending';
        case 'Declined':
          return 'status-declined';
        case 'Sent back to customer':
          return 'status-sent-back';
        default:
          return '';
      }
    } */

  /*  // Get the icon for status to display different icons for each status
   getStatusIcon(status: string): string {
     switch (status) {
       case 'Approved':
         return 'pi pi-check-circle';  // PrimeNG check circle icon
       case 'Pending':
         return 'pi pi-clock';  // PrimeNG clock icon
       case 'Declined':
         return 'pi pi-times-circle';  // PrimeNG times circle icon
       case 'Sent back to customer':
         return 'pi pi-arrow-left';  // PrimeNG left arrow icon
       default:
         return '';
     }
   }
  */
  /*   refreshStatus(new_status: string) {
      this.reservation_details.status = new_status;
    } */


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
