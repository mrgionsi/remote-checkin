import { CommonModule } from '@angular/common';
import { Component, signal } from '@angular/core';
import { RouterModule } from '@angular/router';
import { TranslocoPipe } from '@jsverse/transloco';
import { HeaderComponent } from '../shared/header/header.component';
import { LANDING_NAV_LINKS } from '../shared/navigation';

type BillingCycle = 'monthly' | 'annual';

interface PricingPlan {
  nameKey: string;
  descriptionKey: string;
  monthly: number;
  annual: number;
  featureKeys: string[];
  highlight?: boolean;
  ctaLabelKey: string;
  ctaHref: string;
}

interface ComparisonRow {
  featureKey: string;
  launch: boolean | string;
  growth: boolean | string;
  enterprise: boolean | string;
}

interface AddOn {
  titleKey: string;
  descriptionKey: string;
  priceKey: string;
}

interface PricingFaq {
  questionKey: string;
  answerKey: string;
}

@Component({
  selector: 'app-pricing-details',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslocoPipe, HeaderComponent],
  templateUrl: './pricing-details.component.html',
  styleUrl: './pricing-details.component.scss',
})
export class PricingDetailsComponent {
  readonly billing = signal<BillingCycle>('monthly');

  readonly navLinks = LANDING_NAV_LINKS;

  readonly plans: PricingPlan[] = [
    {
      nameKey: 'pricingDetails.plans.launch.name',
      descriptionKey: 'pricingDetails.plans.launch.description',
      monthly: 0,
      annual: 0,
      featureKeys: [
        'pricingDetails.plans.launch.features.unlimited',
        'pricingDetails.plans.launch.features.journey',
        'pricingDetails.plans.launch.features.emails',
        'pricingDetails.plans.launch.features.community',
      ],
      highlight: false,
      ctaLabelKey: 'pricingDetails.plans.launch.cta',
      ctaHref: '/landing#cta',
    },
    {
      nameKey: 'pricingDetails.plans.growth.name',
      descriptionKey: 'pricingDetails.plans.growth.description',
      monthly: 79,
      annual: 790,
      featureKeys: [
        'pricingDetails.plans.growth.features.everythingLaunch',
        'pricingDetails.plans.growth.features.portal',
        'pricingDetails.plans.growth.features.sms',
        'pricingDetails.plans.growth.features.support',
      ],
      highlight: true,
      ctaLabelKey: 'pricingDetails.plans.growth.cta',
      ctaHref: 'mailto:hello@remote-checkin.io?subject=Growth%20plan%20enquiry',
    },
    {
      nameKey: 'pricingDetails.plans.enterprise.name',
      descriptionKey: 'pricingDetails.plans.enterprise.description',
      monthly: 249,
      annual: 2490,
      featureKeys: [
        'pricingDetails.plans.enterprise.features.everythingGrowth',
        'pricingDetails.plans.enterprise.features.success',
        'pricingDetails.plans.enterprise.features.analytics',
        'pricingDetails.plans.enterprise.features.compliance',
      ],
      highlight: false,
      ctaLabelKey: 'pricingDetails.plans.enterprise.cta',
      ctaHref: 'mailto:hello@remote-checkin.io?subject=Enterprise%20strategy%20session',
    },
  ];

  readonly comparisonRows: ComparisonRow[] = [
    {
      featureKey: 'pricingDetails.comparison.rows.properties',
      launch: 'pricingDetails.comparison.value.unlimited',
      growth: 'pricingDetails.comparison.value.unlimited',
      enterprise: 'pricingDetails.comparison.value.unlimited',
    },
    {
      featureKey: 'pricingDetails.comparison.rows.documents',
      launch: true,
      growth: true,
      enterprise: true,
    },
    {
      featureKey: 'pricingDetails.comparison.rows.portale',
      launch: false,
      growth: true,
      enterprise: true,
    },
    {
      featureKey: 'pricingDetails.comparison.rows.sms',
      launch: false,
      growth: true,
      enterprise: true,
    },
    {
      featureKey: 'pricingDetails.comparison.rows.analytics',
      launch: false,
      growth: 'pricingDetails.comparison.value.limited',
      enterprise: true,
    },
    {
      featureKey: 'pricingDetails.comparison.rows.successManager',
      launch: false,
      growth: false,
      enterprise: true,
    },
  ];

  readonly addOns: AddOn[] = [
    {
      titleKey: 'pricingDetails.addons.handbook.title',
      descriptionKey: 'pricingDetails.addons.handbook.description',
      priceKey: 'pricingDetails.addons.handbook.price',
    },
    {
      titleKey: 'pricingDetails.addons.integrations.title',
      descriptionKey: 'pricingDetails.addons.integrations.description',
      priceKey: 'pricingDetails.addons.integrations.price',
    },
    {
      titleKey: 'pricingDetails.addons.concierge.title',
      descriptionKey: 'pricingDetails.addons.concierge.description',
      priceKey: 'pricingDetails.addons.concierge.price',
    },
  ];

  readonly pricingFaqs: PricingFaq[] = [
    {
      questionKey: 'pricingDetails.faq.mixPlans.question',
      answerKey: 'pricingDetails.faq.mixPlans.answer',
    },
    {
      questionKey: 'pricingDetails.faq.perGuest.question',
      answerKey: 'pricingDetails.faq.perGuest.answer',
    },
    {
      questionKey: 'pricingDetails.faq.annualDiscount.question',
      answerKey: 'pricingDetails.faq.annualDiscount.answer',
    },
    {
      questionKey: 'pricingDetails.faq.onboarding.question',
      answerKey: 'pricingDetails.faq.onboarding.answer',
    },
  ];

  toggleBilling(cycle: BillingCycle): void {
    this.billing.set(cycle);
  }

  getAmountForPlan(plan: PricingPlan): number {
    return this.billing() === 'monthly' ? plan.monthly : plan.annual;
  }

  isFeatureIncluded(value: boolean | string): boolean {
    return value === true;
  }

  getFeatureValueKey(value: boolean | string): string {
    if (typeof value === 'string') {
      return value;
    }
    if (value) {
      return 'pricingDetails.comparison.value.included';
    }
    return 'pricingDetails.comparison.value.notIncluded';
  }
}
