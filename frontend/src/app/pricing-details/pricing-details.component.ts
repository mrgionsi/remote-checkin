import { CommonModule } from '@angular/common';
import { Component, signal } from '@angular/core';
import { RouterModule } from '@angular/router';

type BillingCycle = 'monthly' | 'annual';

interface PricingPlan {
  name: string;
  description: string;
  monthly: number;
  annual: number;
  features: string[];
  highlight?: boolean;
  ctaLabel: string;
  ctaHref: string;
}

interface ComparisonRow {
  feature: string;
  launch: boolean | string;
  growth: boolean | string;
  enterprise: boolean | string;
}

interface AddOn {
  title: string;
  description: string;
  price: string;
}

interface PricingFaq {
  question: string;
  answer: string;
}

@Component({
  selector: 'app-pricing-details',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './pricing-details.component.html',
  styleUrl: './pricing-details.component.scss',
})
export class PricingDetailsComponent {
  readonly billing = signal<BillingCycle>('monthly');

  readonly plans: PricingPlan[] = [
    {
      name: 'Launch',
      description: 'Perfect for independent properties digitalising arrivals for the first time.',
      monthly: 0,
      annual: 0,
      features: [
        'Unlimited reservations and properties',
        'Digital guest journey & identity capture',
        'Email confirmations & reminders',
        'Community support and roadmap voting',
      ],
      highlight: false,
      ctaLabel: 'Start for free',
      ctaHref: '/landing#cta',
    },
    {
      name: 'Growth',
      description: 'For boutique hotels and serviced apartments scaling remote operations.',
      monthly: 79,
      annual: 790,
      features: [
        'Everything in Launch',
        'Brandable guest portal & multi-language templates',
        'SMS reminders & two-way PMS sync',
        'Priority in-app and email support',
      ],
      highlight: true,
      ctaLabel: 'Talk to sales',
      ctaHref: 'mailto:hello@remote-checkin.io?subject=Growth%20plan%20enquiry',
    },
    {
      name: 'Enterprise',
      description: 'Tailored programs for multi-property groups needing governance and integrations.',
      monthly: 249,
      annual: 2490,
      features: [
        'Everything in Growth',
        'Dedicated customer success & launch services',
        'Advanced analytics & custom dashboards',
        'Regional compliance workflows & SSO',
      ],
      highlight: false,
      ctaLabel: 'Book a strategy session',
      ctaHref: 'mailto:hello@remote-checkin.io?subject=Enterprise%20strategy%20session',
    },
  ];

  readonly comparisonRows: ComparisonRow[] = [
    {
      feature: 'Properties & reservations',
      launch: 'Unlimited',
      growth: 'Unlimited',
      enterprise: 'Unlimited',
    },
    {
      feature: 'Guest document capture & signatures',
      launch: true,
      growth: true,
      enterprise: true,
    },
    {
      feature: 'Portale Alloggi automation',
      launch: false,
      growth: true,
      enterprise: true,
    },
    {
      feature: 'SMS reminders & WhatsApp links',
      launch: false,
      growth: true,
      enterprise: true,
    },
    {
      feature: 'Advanced analytics & data export',
      launch: false,
      growth: 'Limited',
      enterprise: true,
    },
    {
      feature: 'Customer success manager',
      launch: false,
      growth: false,
      enterprise: true,
    },
  ];

  readonly addOns: AddOn[] = [
    {
      title: 'Digital guest handbook',
      description: 'Curated content micro-site for each reservation, including upsells and local tips.',
      price: '$25 / property / month',
    },
    {
      title: 'Custom integrations',
      description: 'We build bespoke workflows for PMS, CRM, and loyalty tools that matter to your operations.',
      price: 'From $1,200 (one-off)',
    },
    {
      title: 'Multilingual concierge team',
      description: 'A 24/7 distributed concierge desk that handles arrival questions on your behalf.',
      price: '$150 / month / property',
    },
  ];

  readonly pricingFaqs: PricingFaq[] = [
    {
      question: 'Can we mix plans across properties?',
      answer:
        'Yes. You can run different plans per property and consolidate billing monthly. Enterprise gives you rollout governance.',
    },
    {
      question: 'Do you charge per guest?',
      answer:
        'No. Every plan includes unlimited guests and reservations. You only pay based on the feature set that matches your operation.',
    },
    {
      question: 'How does the annual discount work?',
      answer:
        'Annual billing gives you two months off (pay for 10, get 12). You can upgrade or downgrade at any time with a prorated invoice.',
    },
    {
      question: 'Is onboarding included?',
      answer:
        'Launch includes a self-serve template library. Growth and Enterprise customers receive dedicated onboarding sessions and migration assistance.',
    },
  ];

  toggleBilling(cycle: BillingCycle): void {
    this.billing.set(cycle);
  }

  getPriceForPlan(plan: PricingPlan): string {
    const cycle = this.billing();
    const amount = cycle === 'monthly' ? plan.monthly : plan.annual;

    if (plan.monthly === 0 && plan.annual === 0) {
      return 'Free';
    }

    const prefix = cycle === 'monthly' ? '$' : '$';
    const suffix = cycle === 'monthly' ? '/mo' : '/yr';
    return `${prefix}${amount}${suffix}`;
  }

  isFeatureIncluded(value: boolean | string): boolean {
    return value === true;
  }

  displayFeatureValue(value: boolean | string): string {
    if (typeof value === 'string') {
      return value;
    }
    return value ? 'Included' : '—';
  }
}
