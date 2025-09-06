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
      numberOfPeople: [1, [Validators.required, Validators.min(1)]], // Number of people field
    }, { validators: dateRangeValidator }
    )
  }

  // Inizializzazione nel metodo ngOnInit
  ngOnInit(): void {
    this.getRooms();

    // Add validation for number of people against room capacity
    this.reservationForm.get('roomName')?.valueChanges.subscribe(() => {
      this.validateNumberOfPeople();
    });

    this.reservationForm.get('numberOfPeople')?.valueChanges.subscribe(() => {
      this.validateNumberOfPeople();
    });
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

  // Method to validate number of people against room capacity
  validateNumberOfPeople(): void {
    const selectedRoom = this.reservationForm.get('roomName')?.value;
    const numberOfPeopleControl = this.reservationForm.get('numberOfPeople');
    const numberOfPeople = numberOfPeopleControl?.value;

    // Check if form controls exist
    if (!selectedRoom || !numberOfPeopleControl || numberOfPeople === null || numberOfPeople === undefined) {
      return;
    }

    // Coerce numberOfPeople to numeric type and validate
    const numericNumberOfPeople = Number(numberOfPeople);
    
    // Check if the conversion resulted in NaN or invalid number
    if (isNaN(numericNumberOfPeople) || !isFinite(numericNumberOfPeople)) {
      numberOfPeopleControl.setErrors({
        'invalidNumber': true
      });
      return;
    }

    // Get room capacity with proper fallback
    let roomCapacity = 0;

    // If selectedRoom is an object (from p-select), get capacity directly
    if (typeof selectedRoom === 'object' && selectedRoom.capacity !== undefined) {
      roomCapacity = Number(selectedRoom.capacity) || 0;
    }
    // If selectedRoom is a string (room name), find it in the rooms array
    else if (typeof selectedRoom === 'string' && this.rooms && this.rooms.length > 0) {
      const room = this.rooms.find(room => room.name === selectedRoom);
      roomCapacity = room && room.capacity !== undefined ? Number(room.capacity) || 0 : 0;
    }

    // Only perform capacity validation if room capacity is defined and valid
    if (roomCapacity > 0) {
      // Allow numberOfPeople to equal roomCapacity, but not exceed it
      if (numericNumberOfPeople > roomCapacity) {
        numberOfPeopleControl.setErrors({
          'exceedsCapacity': true,
          'maxCapacity': roomCapacity
        });
      } else {
        // Clear capacity-related errors if validation passes
        const currentErrors = numberOfPeopleControl.errors;
        if (currentErrors) {
          delete currentErrors['exceedsCapacity'];
          delete currentErrors['maxCapacity'];
          numberOfPeopleControl.setErrors(
            Object.keys(currentErrors).length > 0 ? currentErrors : null
          );
        }
      }
    }
  }

  // Method to get selected room capacity for display
  getSelectedRoomCapacity(): number {
    const selectedRoom = this.reservationForm.get('roomName')?.value;

    // If selectedRoom is an object (from p-select), return its capacity directly
    if (selectedRoom && typeof selectedRoom === 'object' && selectedRoom.capacity) {
      return selectedRoom.capacity;
    }

    // If selectedRoom is a string (room name), find it in the rooms array
    if (selectedRoom && typeof selectedRoom === 'string' && this.rooms && this.rooms.length > 0) {
      const room = this.rooms.find(room => room.name === selectedRoom);
      return room ? room.capacity : 0;
    }

    return 0;
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