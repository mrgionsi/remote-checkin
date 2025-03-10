import { AfterViewInit, Component, OnInit } from '@angular/core';
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

@Component({
  selector: 'app-detail-reservation',
  imports: [ToastModule, CommonModule, TableModule, CardModule],
  templateUrl: './detail-reservation.component.html',
  styleUrl: './detail-reservation.component.scss',
  providers: [MessageService, DialogService]

})
export class DetailReservationComponent implements OnInit {
  people: any[] = [];
  reservation_details: any;

  constructor(private reservationService: ReservationService,
    private messageService: MessageService,
    private route: ActivatedRoute,
    private client_reservationService: ClientReservationService,
    private dialogService: DialogService
  ) {

  }
  ngOnInit(): void {
    var reservationId: number;
    this.route.params.subscribe(params => {
      reservationId = params['id_reservation']; // Default to 'en' if missing

      console.log(reservationId)
      this.reservationService.getReservationById(reservationId).subscribe({
        next: (resp) => {
          this.reservation_details = resp;
          console.log(this.reservation_details);
          this.client_reservationService.getClientByReservationId(this.reservation_details.id).subscribe({
            next: (r) => {
              this.people = r;
              this.people.forEach(person => {
                this.client_reservationService.getUserPhoto(reservationId, person.name, person.surname, person.cf).subscribe({
                  next: (person_photo: any) => {
                    console.log(person_photo)
                    person.images = [];
                    person.images.back = person_photo.back_image ? environment.apiBaseUrl + person_photo?.back_image : null;
                    person.images.front = person_photo.front_image ? environment.apiBaseUrl + person_photo?.front_image : null;
                    person.images.selfie = person_photo.selfie ? environment.apiBaseUrl + person_photo?.selfie : null;
                    person.hasMissingImages = !person_photo.back_image || !person_photo.front_image || !person_photo.selfie;

                    console.log(person)
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
    });
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


}
