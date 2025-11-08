import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterModule } from '@angular/router';
import {
  animate,
  group,
  query,
  stagger,
  style,
  transition,
  trigger
} from '@angular/animations';

interface FeatureCard {
  title: string;
  description: string;
  icon: string;
}

interface PricingPlan {
  name: string;
  price: string;
  tagline: string;
  bullets: string[];
  highlight?: boolean;
}

interface NavigationLink {
  label: string;
  href: string;
}

interface FooterColumn {
  heading: string;
  links: { label: string; href: string }[];
}

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.scss',
  animations: [
    trigger('pageFade', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('500ms ease-out', style({ opacity: 1 }))
      ])
    ]),
    trigger('heroReveal', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(1.5rem)' }),
        animate('600ms 120ms ease-out', style({ opacity: 1, transform: 'none' }))
      ])
    ]),
    trigger('staggerReveal', [
      transition(':enter', [
        query(
          '.stagger-item',
          [
            style({ opacity: 0, transform: 'translateY(0.75rem)' }),
            stagger(120, [
              animate('550ms ease-out', style({ opacity: 1, transform: 'none' }))
            ])
          ],
          { optional: true }
        )
      ])
    ]),
    trigger('cardFlip', [
      transition(':enter', [
        style({ transform: 'rotateX(25deg)', opacity: 0 }),
        group([
          animate('400ms ease-out', style({ opacity: 1 })),
          animate('700ms cubic-bezier(.19,1,.22,1)', style({ transform: 'none' }))
        ])
      ])
    ])
  ],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class LandingComponent {
  readonly navLinks: NavigationLink[] = [
    { label: 'Features', href: '#features' },
    { label: 'Pricing', href: '#pricing' },
    { label: 'Self-host', href: '#self-host' },
    { label: 'FAQ', href: '#faq' }
  ];

  readonly featureCards: FeatureCard[] = [
    {
      title: 'Automated Guest Experience',
      description:
        'Remote document capture, identity validation, and digital signatures streamline every arrival.',
      icon: 'pi pi-bolt'
    },
    {
      title: 'Compliance Ready',
      description:
        'Generate and dispatch the required hospitality declarations in minutes, compliant with local regulations.',
      icon: 'pi pi-shield'
    },
    {
      title: 'Real-Time Insights',
      description:
        'Monitor occupancy, guest progress, and revenue forecasts from a single multi-property dashboard.',
      icon: 'pi pi-chart-line'
    },
    {
      title: 'Team Collaboration',
      description:
        'Invite partners, cleaning teams, and front desk staff with role-based permissions that scale with you.',
      icon: 'pi pi-users'
    }
  ];

  readonly pricingPlans: PricingPlan[] = [
    {
      name: 'Launch',
      price: '$0',
      tagline: 'First 20 subscribers — everything you need to get started.',
      bullets: [
        'Unlimited properties & bookings',
        'Digital guest journey with document upload',
        'Automated confirmation emails',
        'Community support & product roadmap voting'
      ],
      highlight: true
    },
    {
      name: 'Growth',
      price: '$79',
      tagline: 'Ideal for boutique hotels and serviced apartments scaling operations.',
      bullets: [
        'Everything in Launch',
        'Brandable guest portal & SMS notifications',
        'Two-way PMS integrations & automation flows',
        'Priority in-app and email support'
      ]
    },
    {
      name: 'Enterprise',
      price: 'Let’s talk',
      tagline: 'Custom implementations for hotel groups and hospitality brands.',
      bullets: [
        'Dedicated onboarding and success manager',
        'Advanced analytics and BI exports',
        'Custom compliance workflows per region',
        'SAML SSO & SOC 2 report upon request'
      ]
    }
  ];

  readonly selfHostBenefits: string[] = [
    'Deploy on your infrastructure with Docker containers and infrastructure-as-code scripts.',
    'Retain full data ownership while leveraging the same features offered in our hosted plans.',
    'Hybrid mode — sync select properties to our cloud, keep the rest on-premises.',
    'Open API and webhook ecosystem for bespoke integrations and automations.'
  ];

  readonly footerColumns: FooterColumn[] = [
    {
      heading: 'Product',
      links: [
        { label: 'Roadmap', href: 'mailto:hello@remote-checkin.io?subject=Roadmap%20Request' },
        { label: 'Security', href: 'mailto:security@remote-checkin.io' },
        { label: 'Status', href: 'mailto:support@remote-checkin.io?subject=Status%20Inquiry' }
      ]
    },
    {
      heading: 'Company',
      links: [
        { label: 'About', href: 'mailto:hello@remote-checkin.io?subject=About%20Remote%20Check-in' },
        { label: 'Careers', href: 'mailto:talent@remote-checkin.io' },
        { label: 'Press Kit', href: 'mailto:press@remote-checkin.io' }
      ]
    },
    {
      heading: 'Resources',
      links: [
        { label: 'Docs', href: 'mailto:hello@remote-checkin.io?subject=Docs%20Access' },
        { label: 'API', href: 'mailto:hello@remote-checkin.io?subject=API%20Access' },
        { label: 'Community Slack', href: 'mailto:hello@remote-checkin.io?subject=Community%20Invite' }
      ]
    }
  ];

  readonly currentYear = new Date().getFullYear();
}

