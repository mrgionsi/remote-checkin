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
  saving = false; // Loading state for save button
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
      email: ['', [Validators.required, Validators.email]], // Email field with validation
      telephone: ['', Validators.required], // Telephone field
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
        console.log('Rooms loaded:', rooms);
        this.rooms = rooms;
      },
      error: (error) => {
        console.error('Error fetching rooms:', error);
      }
    });
  }

  onSubmit(): void {
    if (this.reservationForm.valid) {
      this.saving = true; // Set loading state
      const reservation = this.reservationForm.value;
      console.log(reservation)

      // Handle room name extraction safely
      if (reservation.roomName && reservation.roomName['name']) {
        reservation.roomName = reservation.roomName['name'];
      } else {
        console.error('Room name is not selected or invalid:', reservation.roomName);
        this.saving = false; // Reset loading state on error
        return; // Don't submit if room is not selected
      }

      // Handle date conversion safely using local timezone
      if (reservation.startDate instanceof Date) {
        reservation.startDate = this.formatDateToLocalString(reservation.startDate);
      } else if (reservation.startDate) {
        // If it's already a string, use it as is
        reservation.startDate = reservation.startDate.toString().split('T')[0];
      }

      if (reservation.endDate instanceof Date) {
        reservation.endDate = this.formatDateToLocalString(reservation.endDate);
      } else if (reservation.endDate) {
        // If it's already a string, use it as is
        reservation.endDate = reservation.endDate.toString().split('T')[0];
      }

      // Create an observer object
      const observer = {
        next: (response: any) => {
          console.log('Reservation created successfully', response);
          this.saving = false; // Reset loading state on success
          // Pass reservation data in the state while navigating
          this.router.navigate(['/admin/dashboard'], {
            state: { reservation }
          });
        },
        error: (error: any) => {
          console.error('Error creating reservation', error);
          this.saving = false; // Reset loading state on error
        }
      };

      // Pass the observer object to subscribe
      this.reservationService.createReservation(reservation).subscribe(observer);
    }
  }

  /**
   * Format a Date object to YYYY-MM-DD string using local timezone
   * This avoids timezone shift issues that occur with toISOString()
   */
  private formatDateToLocalString(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }
}  