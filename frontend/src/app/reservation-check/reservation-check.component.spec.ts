import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ReservationCheckComponent } from './reservation-check.component';

describe('ReservationCheckComponent', () => {
  let component: ReservationCheckComponent;
  let fixture: ComponentFixture<ReservationCheckComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReservationCheckComponent]
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
