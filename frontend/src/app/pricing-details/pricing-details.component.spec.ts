import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PricingDetailsComponent } from './pricing-details.component';

describe('PricingDetailsComponent', () => {
  let component: PricingDetailsComponent;
  let fixture: ComponentFixture<PricingDetailsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PricingDetailsComponent]
    })
      .overrideComponent(PricingDetailsComponent, { set: { template: '' } })
      .compileComponents();

    fixture = TestBed.createComponent(PricingDetailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should return zero amount for free plan', () => {
    const freePlan = component.plans[0];
    expect(component.getAmountForPlan(freePlan)).toBe(0);
  });
});
