import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { SelectModule } from 'primeng/select';
import { InputTextModule } from 'primeng/inputtext';
import { DatePickerModule } from 'primeng/datepicker';
import { ButtonModule } from 'primeng/button';
import { Router } from '@angular/router';  // Optional: to redirect after successful reservation
import { ReservationService } from '../../services/reservation.service';
import { CommonModule } from '@angular/common';


@Component({
  selector: 'app-create-reservation',
  imports: [DatePickerModule, InputTextModule, ButtonModule, CommonModule, ReactiveFormsModule, SelectModule],
  templateUrl: './create-reservation.component.html',
  providers: [ReservationService], // <-- Manually provide the service in the component
  styleUrl: './create-reservation.component.scss'
})
export class CreateReservationComponent implements OnInit {

  reservationForm: FormGroup; // Dichiarazione della proprietà
  reservationService = inject(ReservationService)
  // Array of room options for the dropdown
  rooms: any[] = [
    { name: 'Savana', code: 'savana' },
    { name: 'SPA', code: 'spa' },
    { name: 'Giungla', code: 'giungla' }
  ];
  constructor(
    private fb: FormBuilder,
    private router: Router
  ) {
    this.reservationForm = this.fb.group({
      reservationNumber: ['', Validators.required],
      startDate: ['', Validators.required],
      endDate: ['', Validators.required],
      roomName: ['', Validators.required],
    });
  }

  // Inizializzazione nel metodo ngOnInit
  ngOnInit(): void {

  }

  onSubmit(): void {
    if (this.reservationForm.valid) {
      const reservation = this.reservationForm.value;
      console.log(reservation)

      reservation.startDate = reservation.startDate.toISOString().split('T')[0];
      reservation.endDate = reservation.endDate.toISOString().split('T')[0];

      // Create an observer object
      const observer = {
        next: (response: any) => {
          console.log('Reservation created successfully', response);
          this.router.navigate(['/success']);
        },
        error: (error: any) => {
          console.error('Error creating reservation', error);
        }
      };

      // Pass the observer object to subscribe
      this.reservationService.createReservation(reservation).subscribe(observer);
    }
  }
}  