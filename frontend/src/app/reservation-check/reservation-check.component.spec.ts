import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ReservationCheckComponent } from './reservation-check.component';
import { ActivatedRoute, Router } from '@angular/router';
import { of } from 'rxjs';
import { ReservationService } from '../services/reservation.service';

describe('ReservationCheckComponent', () => {
  let component: ReservationCheckComponent;
  let fixture: ComponentFixture<ReservationCheckComponent>;

  beforeEach(async () => {
    const routerSpy = jasmine.createSpyObj('Router', ['navigate']);
    const activatedRouteSpy = {
      paramMap: of({ get: (param: string) => param === 'code' ? 'TEST123' : null })
    };

    await TestBed.configureTestingModule({
      imports: [ReservationCheckComponent],
      providers: [
        { provide: Router, useValue: routerSpy },
        { provide: ActivatedRoute, useValue: activatedRouteSpy },
        { provide: ReservationService, useValue: jasmine.createSpyObj('ReservationService', ['getReservationById']) }
      ]
    })
      .compileComponents();

    fixture = TestBed.createComponent(ReservationCheckComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
