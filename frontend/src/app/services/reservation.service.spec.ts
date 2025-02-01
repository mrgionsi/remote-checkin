import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReservationService } from './reservation.service';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { By } from '@angular/platform-browser';
import { of } from 'rxjs';
import { CreateReservationComponent } from '../admin/create-reservation/create-reservation.component';

describe('CreateReservationComponent', () => {
  let component: CreateReservationComponent;
  let fixture: ComponentFixture<CreateReservationComponent>;
  let reservationService: ReservationService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [CreateReservationComponent],
      imports: [ReactiveFormsModule, HttpClientTestingModule],
      providers: [ReservationService],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(CreateReservationComponent);
    component = fixture.componentInstance;
    reservationService = TestBed.inject(ReservationService);
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should call the createReservation method of the service when form is valid', () => {
    const spy = spyOn(reservationService, 'createReservation').and.returnValue(of({}));

    // Set up form values
    component.reservationForm.setValue({
      reservationNumber: '123',
      startDate: '2025-02-01',
      endDate: '2025-02-05',
      roomName: 'Deluxe Suite',
    });

    // Trigger form submit
    component.onSubmit();

    // Verify the service was called
    expect(spy).toHaveBeenCalled();
  });

  it('should display error message if form is invalid', () => {
    // Trigger submit with empty form
    component.onSubmit();

    // Check if validation error message is displayed
    const errorMessages = fixture.debugElement.queryAll(By.css('.p-error'));
    expect(errorMessages.length).toBeGreaterThan(0);
  });
});
