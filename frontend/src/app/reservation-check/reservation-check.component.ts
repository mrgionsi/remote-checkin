import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
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
export class ReservationCheckComponent {
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

    this.reservationService.getReservationById(Number(this.reservationId)).subscribe({
      next: (val) => {
        console.log(val);
        if (this.reservationId.trim()) {
          this.router.navigate([`/${this.reservationId}/remote-checkin/${this.languageCode}`]);
        }
      },
      error: (error) => {
        _.messageService.add({ severity: 'warn', summary: 'Error', detail: 'Not possible to validate reservation. Please try again or contact your administrator.' });
        console.error(error);
      }
    })

  }
}
