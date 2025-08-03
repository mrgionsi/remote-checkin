import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { ReservationService } from '../services/reservation.service';
import { ToastModule } from 'primeng/toast';

@Component({
  selector: 'app-reservation-check',
  imports: [CommonModule, FormsModule, InputTextModule, ButtonModule, ToastModule],
  templateUrl: './reservation-check.component.html',
  styleUrl: './reservation-check.component.scss',
  providers: [MessageService]
})
export class ReservationCheckComponent implements OnInit {
  reservationId: string = '';
  languageCode: string = '';

  constructor(private route: ActivatedRoute, private router: Router,
    private reservationService: ReservationService,
    private messageService: MessageService
  ) { }

  ngOnInit() {
    // Fetch the language code from the URL
    this.route.params.subscribe(params => {
      this.languageCode = params['code'] || 'en'; // Default to 'en' if missing

    });
  }
  goToCheckIn() {
    var _ = this;

    this.reservationService.checkReservationById(Number(this.reservationId)).subscribe({
      next: (val) => {
        if (val && val.id_reference) {
          _.messageService.add({ severity: 'success', summary: 'Success', detail: 'Reservation validated successfully.' });
        } else {
          _.messageService.add({ severity: 'error', summary: 'Error', detail: 'Invalid reservation ID. Please check and try again.' });
          return;
        }
        // Navigate to the remote check-in page with the reservation ID and language code

        if (!this.reservationId || !this.languageCode) {
          console.error('Missing values! Cannot navigate.');
        } else {
          var url = 'remote-checkin';
          this.router.navigate([this.reservationId, url, this.languageCode]);
        }
      },
      error: (error) => {
        _.messageService.add({ severity: 'warn', summary: 'Error', detail: 'Not possible to validate reservation. Please try again or contact your administrator.' });
        console.error(error);
      }
    })

  }
}
