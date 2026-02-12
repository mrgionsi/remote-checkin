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
import { TranslocoPipe, TranslocoService } from '@jsverse/transloco';

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
  canCreateReservation = true;
  constructor(
    private fb: FormBuilder,
    private router: Router,
    private roomService: RoomService,
    private translocoService: TranslocoService
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
    this.setDefaultDates();

    // Add validation for number of people against room capacity
    this.reservationForm.get('roomName')?.valueChanges.subscribe((value) => {
      const numberOfPeopleControl = this.reservationForm.get('numberOfPeople');
      if (numberOfPeopleControl) {
        if (value) {
          numberOfPeopleControl.enable({ emitEvent: false });
        } else {
          numberOfPeopleControl.disable({ emitEvent: false });
        }
      }
      this.validateNumberOfPeople();
    });

    this.reservationForm.get('numberOfPeople')?.valueChanges.subscribe(() => {
      this.validateNumberOfPeople();
    });

    const initialRoom = this.reservationForm.get('roomName')?.value;
    const numberOfPeopleControl = this.reservationForm.get('numberOfPeople');
    if (numberOfPeopleControl) {
      if (initialRoom) {
        numberOfPeopleControl.enable({ emitEvent: false });
      } else {
        numberOfPeopleControl.disable({ emitEvent: false });
      }
    }
  }

  private setDefaultDates(): void {
    const start = this.reservationForm.get('startDate')?.value;
    const end = this.reservationForm.get('endDate')?.value;
    if (!start && !end) {
      const now = new Date();
      const tomorrow = new Date(now);
      tomorrow.setDate(now.getDate() + 1);
      this.reservationForm.patchValue({
        startDate: now,
        endDate: tomorrow
      });
    }
  }
  // Method to get rooms from the backend
  getRooms(): void {
    const selectedStructureId = Number(localStorage.getItem('selected_structure_id') || 0);
    if (!selectedStructureId) {
      this.canCreateReservation = false;
      this.rooms = [];
      return;
    }
    this.canCreateReservation = true;
    this.roomService.getRooms(selectedStructureId || null).subscribe({
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
    if (!this.canCreateReservation) {
      this.setRoomControlError('structureRequired');
      return;
    }
    if (this.reservationForm.valid) {
      this.saving = true; // Set loading state
      const reservation = this.reservationForm.value;
      console.log(reservation)

      // Handle room name extraction safely and include room/structure identifiers
      if (reservation.roomName && reservation.roomName['name']) {
        reservation.roomId = reservation.roomName['id'];
        reservation.structureId = reservation.roomName['id_structure'] ?? Number(localStorage.getItem('selected_structure_id') || 0);
        reservation.roomName = reservation.roomName['name'];
      } else if (typeof reservation.roomName === 'string') {
        const roomMatch = this.rooms.find(room => room.name === reservation.roomName);
        if (roomMatch) {
          reservation.roomId = roomMatch.id;
          reservation.structureId = roomMatch.id_structure ?? Number(localStorage.getItem('selected_structure_id') || 0);
        } else {
          reservation.structureId = Number(localStorage.getItem('selected_structure_id') || 0);
          if (!reservation.structureId) {
            this.setRoomControlError('structureRequired');
            this.saving = false;
            return;
          }
          this.setRoomControlError('roomNotFound');
          this.saving = false;
          return;
        }
      } else {
        console.error('Room name is not selected or invalid:', reservation.roomName);
        this.setRoomControlError('roomNotFound');
        this.saving = false; // Reset loading state on error
        return; // Don't submit if room is not selected
      }

      if (!reservation.roomId) {
        this.setRoomControlError('roomNotFound');
        this.saving = false;
        return;
      }

      if (!reservation.structureId) {
        this.setRoomControlError('structureRequired');
        this.saving = false;
        return;
      }

      this.clearRoomResolutionErrors();

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
          const backendError = error?.error?.error;
          if (backendError === 'structureId is required when using roomName') {
            this.setRoomControlError('structureRequired');
          }
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

  getRoomResolutionErrorMessage(): string {
    const roomControl = this.reservationForm.get('roomName');
    if (!roomControl?.errors) {
      return '';
    }
    if (roomControl.errors['structureRequired']) {
      return this.translocoService.translate('reservation-structure-required');
    }
    if (roomControl.errors['roomNotFound']) {
      return this.translocoService.translate('reservation-room-not-found');
    }
    return '';
  }

  private setRoomControlError(errorKey: 'structureRequired' | 'roomNotFound'): void {
    const roomControl = this.reservationForm.get('roomName');
    if (!roomControl) {
      return;
    }
    roomControl.setErrors({ ...(roomControl.errors || {}), [errorKey]: true });
    roomControl.markAsTouched();
  }

  private clearRoomResolutionErrors(): void {
    const roomControl = this.reservationForm.get('roomName');
    if (!roomControl?.errors) {
      return;
    }
    const errors = { ...roomControl.errors };
    delete errors['structureRequired'];
    delete errors['roomNotFound'];
    roomControl.setErrors(Object.keys(errors).length ? errors : null);
  }
}
