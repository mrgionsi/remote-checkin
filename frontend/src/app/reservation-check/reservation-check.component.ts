import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';

@Component({
  selector: 'app-reservation-check',
  imports: [CommonModule, FormsModule, InputTextModule, ButtonModule],
  templateUrl: './reservation-check.component.html',
  styleUrl: './reservation-check.component.scss'
})
export class ReservationCheckComponent {
  reservationId: string = '';
  languageCode: string = '';

  constructor(private route: ActivatedRoute, private router: Router) { }

  ngOnInit() {
    // Fetch the language code from the URL
    this.route.params.subscribe(params => {
      this.languageCode = params['code'] || 'en'; // Default to 'en' if missing
    });
  }
  goToCheckIn() {
    if (this.reservationId.trim()) {
      this.router.navigate([`/${this.reservationId}/remote-checkin/${this.languageCode}`]);
    }
  }
}
