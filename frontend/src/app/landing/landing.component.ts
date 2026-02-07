import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
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
import { TranslocoPipe } from '@jsverse/transloco';
import { FormsModule } from '@angular/forms';
import { HeaderComponent } from '../shared/header/header.component';
import { LANDING_NAV_LINKS } from '../shared/navigation';

interface FeatureCard {
  titleKey: string;
  descriptionKey: string;
  icon: string;
}

interface AdvantageCard {
  titleKey: string;
  descriptionKey: string;
  icon: string;
  metric: string;
  benefitKeys: string[];
}

interface PricingPlan {
  nameKey: string;
  price?: string;
  priceMonthly?: string;
  priceAnnual?: string;
  priceLabelKey?: string;
  priceNoteKey: string;
  taglineKey: string;
  bulletKeys: string[];
  paymentMethods?: { name: string; icon: string }[];
  highlight?: boolean;
}


interface FooterColumn {
  headingKey: string;
  links: { labelKey: string; href?: string; routerLink?: string }[];
}

interface HowItWorksStep {
  stageKey: string;
  titleKey: string;
  descriptionKey: string;
  icon: string;
}

interface Testimonial {
  quoteKey: string;
  authorKey: string;
  roleKey: string;
}

interface ResourceHighlight {
  titleKey: string;
  descriptionKey: string;
  actionLabelKey: string;
  actionHref: string;
}

interface PersonaOption {
  id: 'operators' | 'guests';
  labelKey: string;
}

interface PersonaContent {
  titleKey: string;
  descriptionKey: string;
  bulletKeys: string[];
}

interface JourneyStep {
  titleKey: string;
  descriptionKey: string;
  icon: string;
}

interface ComplianceItem {
  titleKey: string;
  descriptionKey: string;
  icon: string;
}

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslocoPipe, FormsModule, HeaderComponent],
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
  readonly showStickyCta = signal(true);
  readonly showSocialProof = true;
  readonly isAnnualBilling = signal(false);
  readonly persona = signal<'operators' | 'guests'>('operators');

  constructor() {}

  readonly navLinks = LANDING_NAV_LINKS;

  readonly advantageCards: AdvantageCard[] = [
    {
      titleKey: 'landing.advantages.cards.timeSavings.title',
      descriptionKey: 'landing.advantages.cards.timeSavings.description',
      icon: 'pi pi-clock',
      metric: '2h/day',
      benefitKeys: [
        'landing.advantages.cards.timeSavings.benefits.checkin',
        'landing.advantages.cards.timeSavings.benefits.paperwork',
        'landing.advantages.cards.timeSavings.benefits.staff'
      ]
    },
    {
      titleKey: 'landing.advantages.cards.costReduction.title',
      descriptionKey: 'landing.advantages.cards.costReduction.description',
      icon: 'pi pi-dollar',
      metric: '-30%',
      benefitKeys: [
        'landing.advantages.cards.costReduction.benefits.staffing',
        'landing.advantages.cards.costReduction.benefits.printing',
        'landing.advantages.cards.costReduction.benefits.errors'
      ]
    },
    {
      titleKey: 'landing.advantages.cards.guestExperience.title',
      descriptionKey: 'landing.advantages.cards.guestExperience.description',
      icon: 'pi pi-smile',
      metric: '+45%',
      benefitKeys: [
        'landing.advantages.cards.guestExperience.benefits.speed',
        'landing.advantages.cards.guestExperience.benefits.convenience',
        'landing.advantages.cards.guestExperience.benefits.satisfaction'
      ]
    },
    {
      titleKey: 'landing.advantages.cards.compliance.title',
      descriptionKey: 'landing.advantages.cards.compliance.description',
      icon: 'pi pi-shield',
      metric: '100%',
      benefitKeys: [
        'landing.advantages.cards.compliance.benefits.automated',
        'landing.advantages.cards.compliance.benefits.legal',
        'landing.advantages.cards.compliance.benefits.audit'
      ]
    }
  ];

  readonly personaOptions: PersonaOption[] = [
    { id: 'operators', labelKey: 'landing.persona.operators.label' },
    { id: 'guests', labelKey: 'landing.persona.guests.label' }
  ];

  readonly personaContent: Record<'operators' | 'guests', PersonaContent> = {
    operators: {
      titleKey: 'landing.persona.operators.title',
      descriptionKey: 'landing.persona.operators.description',
      bulletKeys: [
        'landing.persona.operators.bullets.ops',
        'landing.persona.operators.bullets.compliance',
        'landing.persona.operators.bullets.brand'
      ]
    },
    guests: {
      titleKey: 'landing.persona.guests.title',
      descriptionKey: 'landing.persona.guests.description',
      bulletKeys: [
        'landing.persona.guests.bullets.mobile',
        'landing.persona.guests.bullets.speed',
        'landing.persona.guests.bullets.control'
      ]
    }
  };

  readonly journeySteps: JourneyStep[] = [
    {
      titleKey: 'landing.journey.steps.invite.title',
      descriptionKey: 'landing.journey.steps.invite.description',
      icon: 'pi pi-send'
    },
    {
      titleKey: 'landing.journey.steps.verify.title',
      descriptionKey: 'landing.journey.steps.verify.description',
      icon: 'pi pi-id-card'
    },
    {
      titleKey: 'landing.journey.steps.confirm.title',
      descriptionKey: 'landing.journey.steps.confirm.description',
      icon: 'pi pi-check-circle'
    }
  ];

  readonly complianceItems: ComplianceItem[] = [
    {
      titleKey: 'landing.compliance.items.gdpr.title',
      descriptionKey: 'landing.compliance.items.gdpr.description',
      icon: 'pi pi-shield'
    },
    {
      titleKey: 'landing.compliance.items.encryption.title',
      descriptionKey: 'landing.compliance.items.encryption.description',
      icon: 'pi pi-lock'
    },
    {
      titleKey: 'landing.compliance.items.portale.title',
      descriptionKey: 'landing.compliance.items.portale.description',
      icon: 'pi pi-globe'
    }
  ];

  readonly featureCards: FeatureCard[] = [
    {
      titleKey: 'landing.features.cards.automated.title',
      descriptionKey: 'landing.features.cards.automated.description',
      icon: 'pi pi-bolt'
    },
    {
      titleKey: 'landing.features.cards.compliance.title',
      descriptionKey: 'landing.features.cards.compliance.description',
      icon: 'pi pi-shield'
    },
    {
      titleKey: 'landing.features.cards.insights.title',
      descriptionKey: 'landing.features.cards.insights.description',
      icon: 'pi pi-chart-line'
    },
    {
      titleKey: 'landing.features.cards.collaboration.title',
      descriptionKey: 'landing.features.cards.collaboration.description',
      icon: 'pi pi-users'
    },
    {
      titleKey: 'landing.features.cards.mobile.title',
      descriptionKey: 'landing.features.cards.mobile.description',
      icon: 'pi pi-mobile'
    },
    {
      titleKey: 'landing.features.cards.integration.title',
      descriptionKey: 'landing.features.cards.integration.description',
      icon: 'pi pi-plug'
    }
  ];

  readonly pricingPlans: PricingPlan[] = [
    {
      nameKey: 'landing.pricing.plans.launch.name',
      priceMonthly: '$0',
      priceAnnual: '$0',
      priceNoteKey: 'landing.pricing.pricePerMonth',
      taglineKey: 'landing.pricing.plans.launch.tagline',
      paymentMethods: [
        { name: 'Card', icon: 'credit-card' },
        { name: 'Bank', icon: 'building' }
      ],
      bulletKeys: [
        'landing.pricing.plans.launch.bullets.properties',
        'landing.pricing.plans.launch.bullets.journey',
        'landing.pricing.plans.launch.bullets.emails',
        'landing.pricing.plans.launch.bullets.community'
      ],
      highlight: true
    },
    {
      nameKey: 'landing.pricing.plans.growth.name',
      priceMonthly: '$79',
      priceAnnual: '$790',
      priceNoteKey: 'landing.pricing.pricePerMonth',
      taglineKey: 'landing.pricing.plans.growth.tagline',
      paymentMethods: [
        { name: 'Card', icon: 'credit-card' },
        { name: 'PayPal', icon: 'paypal' },
        { name: 'Bank', icon: 'building' }
      ],
      bulletKeys: [
        'landing.pricing.plans.growth.bullets.allLaunch',
        'landing.pricing.plans.growth.bullets.brandable',
        'landing.pricing.plans.growth.bullets.integrations',
        'landing.pricing.plans.growth.bullets.support',
        'landing.pricing.plans.growth.bullets.analytics'
      ]
    },
    {
      nameKey: 'landing.pricing.plans.enterprise.name',
      priceNoteKey: 'landing.pricing.plans.enterprise.priceNote',
      taglineKey: 'landing.pricing.plans.enterprise.tagline',
      paymentMethods: [
        { name: 'Card', icon: 'credit-card' },
        { name: 'PayPal', icon: 'paypal' },
        { name: 'Bank', icon: 'building' },
        { name: 'Invoice', icon: 'file' }
      ],
      bulletKeys: [
        'landing.pricing.plans.enterprise.bullets.onboarding',
        'landing.pricing.plans.enterprise.bullets.analytics',
        'landing.pricing.plans.enterprise.bullets.workflows',
        'landing.pricing.plans.enterprise.bullets.security',
        'landing.pricing.plans.enterprise.bullets.dedicated'
      ]
    }
  ];

  readonly selfHostBenefits: string[] = [
    'landing.selfHost.benefits.deploy',
    'landing.selfHost.benefits.ownership',
    'landing.selfHost.benefits.hybrid',
    'landing.selfHost.benefits.api'
  ];

  readonly howItWorksSteps: HowItWorksStep[] = [
    {
      stageKey: 'landing.howItWorks.steps.invite.stage',
      titleKey: 'landing.howItWorks.steps.invite.title',
      descriptionKey: 'landing.howItWorks.steps.invite.description',
      icon: 'pi pi-send'
    },
    {
      stageKey: 'landing.howItWorks.steps.capture.stage',
      titleKey: 'landing.howItWorks.steps.capture.title',
      descriptionKey: 'landing.howItWorks.steps.capture.description',
      icon: 'pi pi-id-card'
    },
    {
      stageKey: 'landing.howItWorks.steps.sync.stage',
      titleKey: 'landing.howItWorks.steps.sync.title',
      descriptionKey: 'landing.howItWorks.steps.sync.description',
      icon: 'pi pi-sync'
    },
    {
      stageKey: 'landing.howItWorks.steps.payment.stage',
      titleKey: 'landing.howItWorks.steps.payment.title',
      descriptionKey: 'landing.howItWorks.steps.payment.description',
      icon: 'pi pi-credit-card'
    }
  ];

  readonly footerColumns: FooterColumn[] = [
    {
      headingKey: 'landing.footer.columns.product.heading',
      links: [
        { labelKey: 'landing.footer.columns.product.links.roadmap', href: 'mailto:hello@remote-checkin.io?subject=Roadmap%20Request' },
        { labelKey: 'landing.footer.columns.product.links.security', href: 'mailto:security@remote-checkin.io' },
        { labelKey: 'landing.footer.columns.product.links.status', href: 'mailto:support@remote-checkin.io?subject=Status%20Inquiry' }
      ]
    },
    {
      headingKey: 'landing.footer.columns.company.heading',
      links: [
        { labelKey: 'landing.footer.columns.company.links.about', href: 'mailto:hello@remote-checkin.io?subject=About%20Remote%20Check-in' },
        { labelKey: 'landing.footer.columns.company.links.careers', href: 'mailto:talent@remote-checkin.io' },
        { labelKey: 'landing.footer.columns.company.links.press', href: 'mailto:press@remote-checkin.io' }
      ]
    },
    {
      headingKey: 'landing.footer.columns.resources.heading',
      links: [
        { labelKey: 'landing.footer.columns.resources.links.docs', href: 'mailto:hello@remote-checkin.io?subject=Docs%20Access' },
        { labelKey: 'landing.footer.columns.resources.links.api', href: 'mailto:hello@remote-checkin.io?subject=API%20Access' },
        { labelKey: 'landing.footer.columns.resources.links.slack', href: 'mailto:hello@remote-checkin.io?subject=Community%20Invite' },
        { labelKey: 'landing.footer.columns.resources.links.pricing', routerLink: '/pricing' },
        { labelKey: 'landing.footer.columns.resources.links.faq', routerLink: '/faq' }
      ]
    }
  ];

  readonly currentYear = new Date().getFullYear();

  readonly trustedBrands: string[] = [
    'Breeze Hotels',
    'Summit Stays',
    'Lakeside Resorts',
    'Atlas Hospitality',
    'UrbanNest Co.'
  ];

  readonly testimonials: Testimonial[] = [
    {
      quoteKey: 'landing.testimonials.items.claudia.quote',
      authorKey: 'landing.testimonials.items.claudia.author',
      roleKey: 'landing.testimonials.items.claudia.role'
    },
    {
      quoteKey: 'landing.testimonials.items.david.quote',
      authorKey: 'landing.testimonials.items.david.author',
      roleKey: 'landing.testimonials.items.david.role'
    },
    {
      quoteKey: 'landing.testimonials.items.lina.quote',
      authorKey: 'landing.testimonials.items.lina.author',
      roleKey: 'landing.testimonials.items.lina.role'
    }
  ];

  readonly resourceHighlights: ResourceHighlight[] = [
    {
      titleKey: 'landing.resources.cards.playbook.title',
      descriptionKey: 'landing.resources.cards.playbook.description',
      actionLabelKey: 'landing.resources.cards.playbook.action',
      actionHref: 'mailto:hello@remote-checkin.io?subject=Playbook%20request'
    },
    {
      titleKey: 'landing.resources.cards.walkthrough.title',
      descriptionKey: 'landing.resources.cards.walkthrough.description',
      actionLabelKey: 'landing.resources.cards.walkthrough.action',
      actionHref: 'mailto:hello@remote-checkin.io?subject=Demo%20walkthrough'
    },
    {
      titleKey: 'landing.resources.cards.docs.title',
      descriptionKey: 'landing.resources.cards.docs.description',
      actionLabelKey: 'landing.resources.cards.docs.action',
      actionHref: 'mailto:hello@remote-checkin.io?subject=API%20Docs%20request'
    }
  ];

  setPersona(id: 'operators' | 'guests'): void {
    this.persona.set(id);
  }

  dismissStickyCta(): void {
    this.showStickyCta.set(false);
  }

  
}
