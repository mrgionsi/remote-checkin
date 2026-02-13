import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PricingDetailsComponent } from './pricing-details.component';
import { TranslocoService } from '@jsverse/transloco';

describe('PricingDetailsComponent', () => {
  let component: PricingDetailsComponent;
  let fixture: ComponentFixture<PricingDetailsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PricingDetailsComponent],
      providers: [
        {
          provide: TranslocoService,
          useValue: {
            translate: (key: string) => {
              const map: Record<string, string> = {
                'pricingDetails.pricing.currencySymbol': '$',
                'pricingDetails.pricing.perMonth': '/mo',
                'pricingDetails.pricing.perYear': '/yr',
                'pricingDetails.pricing.free': 'Free',
                'pricingDetails.comparison.value.included': 'Included',
                'pricingDetails.comparison.value.notIncluded': 'Not included'
              };
              return map[key] || key;
            }
          }
        }
      ]
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

  it('should return free label for free plan', () => {
    const freePlan = component.plans[0];
    expect(component.getPriceForPlan(freePlan)).toBe('Free');
  });
});
