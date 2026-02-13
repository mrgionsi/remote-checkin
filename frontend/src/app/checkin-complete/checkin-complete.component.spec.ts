import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';

import { CheckinCompleteComponent } from './checkin-complete.component';

describe('CheckinCompleteComponent', () => {
  let component: CheckinCompleteComponent;
  let fixture: ComponentFixture<CheckinCompleteComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CheckinCompleteComponent],
      providers: [
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { paramMap: convertToParamMap({ id: '123' }) }
          }
        }
      ]
    })
      .overrideComponent(CheckinCompleteComponent, { set: { template: '' } })
      .compileComponents();

    fixture = TestBed.createComponent(CheckinCompleteComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should read reservation id from route', () => {
    expect(component.reservationId).toBe('123');
  });
});
