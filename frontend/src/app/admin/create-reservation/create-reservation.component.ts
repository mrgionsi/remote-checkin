import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { SelectModule } from 'primeng/select';
import { InputTextModule } from 'primeng/inputtext';
import { DatePickerModule } from 'primeng/datepicker';
import { ButtonModule } from 'primeng/button';
import { Router } from '@angular/router';  // Optional: to redirect after successful reservation
import { ReservationService } from '../../services/reservation.service';
import { CommonModule } from '@angular/common';
import { RoomService } from '../../services/room.service';
import { dateRangeValidator } from '../../validators/date-range.validator';
import { TranslocoPipe } from '@jsverse/transloco';

@Component({
  selector: 'app-create-reservation',
  imports: [DatePickerModule, InputTextModule, ButtonModule, CommonModule, ReactiveFormsModule, SelectModule, TranslocoPipe],
  templateUrl: './create-reservation.component.html',
  styleUrl: './create-reservation.component.scss'
})
export class CreateReservationComponent implements OnInit {

  reservationForm: FormGroup; // Dichiarazione della proprietà
  reservationService = inject(ReservationService)
  // Array of room options for the dropdown
  rooms: any[] = [];
  constructor(
    private fb: FormBuilder,
    private router: Router,
    private roomService: RoomService
  ) {
    this.reservationForm = this.fb.group({
      reservationNumber: ['', Validators.required],
      startDate: ['', Validators.required],
      endDate: ['', Validators.required],
      roomName: ['', Validators.required],
      nameReference: ['', Validators.required], // New field added
    }, { validators: dateRangeValidator }
    )
  }

  // Inizializzazione nel metodo ngOnInit
  ngOnInit(): void {
    this.getRooms();

  }
  // Method to get rooms from the backend
  getRooms(): void {
    this.roomService.getRooms().subscribe({
      next: (rooms) => {
        this.rooms = rooms;

      },
      error: (error) => {
        console.error('Error fetching rooms:', error);
      }
    });
  }

  onSubmit(): void {
    if (this.reservationForm.valid) {
      const reservation = this.reservationForm.value;
      console.log(reservation)
      reservation.roomName = reservation.roomName['name']
      reservation.startDate = reservation.startDate.toISOString().split('T')[0];
      reservation.endDate = reservation.endDate.toISOString().split('T')[0];

      // Create an observer object
      const observer = {
        next: (response: any) => {
          console.log('Reservation created successfully', response);
          // Pass reservation data in the state while navigating
          this.router.navigate(['/admin/dashboard'], {
            state: { reservation }
          });
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