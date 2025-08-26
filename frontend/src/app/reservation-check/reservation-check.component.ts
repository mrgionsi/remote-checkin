import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { ReservationService } from '../services/reservation.service';
import { ToastModule } from 'primeng/toast';
import { TranslocoPipe, TranslocoService } from '@jsverse/transloco';

@Component({
  selector: 'app-reservation-check',
  imports: [CommonModule, FormsModule, InputTextModule, ButtonModule, ToastModule, TranslocoPipe],
  templateUrl: './reservation-check.component.html',
  styleUrl: './reservation-check.component.scss',
  providers: [MessageService]
})
export class ReservationCheckComponent implements OnInit {
  reservationId: string = '';
  languageCode: string = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private reservationService: ReservationService,
    private messageService: MessageService,
    private translocoService: TranslocoService
  ) { }

  ngOnInit() {
    // Fetch the language code from the URL
    this.route.params.subscribe(params => {
      this.languageCode = params['code'] || 'en'; // Default to 'en' if missing
      this.translocoService.setActiveLang(this.languageCode); // Imposta la lingua attiva
    });
  }
  goToCheckIn() {
    var _ = this;

    this.reservationService.checkReservationById(Number(this.reservationId)).subscribe({
      next: (val) => {
        const successMsg = this.translocoService.translate('reservation-success');
        const errorMsg = this.translocoService.translate('reservation-error');

        if (val && val.id_reference) {
          _.messageService.add({
            severity: 'success',
            summary: this.translocoService.translate('success'),
            detail: this.translocoService.translate('reservation-success')
          });
        } else {
          _.messageService.add({
            severity: 'error',
            summary: this.translocoService.translate('error'),
            detail: this.translocoService.translate('reservation-error')
          });
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
        this.messageService.add({
          severity: 'warn',
          summary: this.translocoService.translate('error'),
          detail: this.translocoService.translate('reservation-check-fail')
        });
        console.error('Error checking reservation:', error);
      },
    });
  }
}
