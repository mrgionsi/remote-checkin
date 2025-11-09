import { CommonModule, isPlatformBrowser } from '@angular/common';
import { AfterViewInit, ChangeDetectionStrategy, Component, Inject, signal } from '@angular/core';
import { PLATFORM_ID } from '@angular/core';
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

interface FeatureCard {
  titleKey: string;
  descriptionKey: string;
  icon: string;
}

interface PricingPlan {
  nameKey: string;
  price?: string;
  priceLabelKey?: string;
  priceNoteKey: string;
  taglineKey: string;
  bulletKeys: string[];
  highlight?: boolean;
}

interface NavigationLink {
  labelKey: string;
  href: string;
}

interface FooterColumn {
  headingKey: string;
  links: { labelKey: string; href: string }[];
}

interface HowItWorksStep {
  stageKey: string;
  titleKey: string;
  descriptionKey: string;
  icon: string;
}

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslocoPipe],
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
export class LandingComponent implements AfterViewInit {
  readonly showStickyCta = signal(true);

  readonly liveProperties = signal(0);
  readonly selfCheckins = signal(0);
  readonly timeSaved = signal(0);
  readonly upsellLift = signal(0);

  private readonly livePropertyTarget = 48;
  private readonly selfCheckinsTarget = 92;
  private readonly timeSavedTarget = 1.8;
  private readonly upsellTarget = 36;
  private readonly isBrowser: boolean;

  constructor(@Inject(PLATFORM_ID) platformId: object) {
    this.isBrowser = isPlatformBrowser(platformId);
  }

  readonly navLinks: NavigationLink[] = [
    { labelKey: 'landing.nav.howItWorks', href: '#how-it-works' },
    { labelKey: 'landing.nav.features', href: '#features' },
    { labelKey: 'landing.nav.pricing', href: '#pricing' },
    { labelKey: 'landing.nav.selfHost', href: '#self-host' },
    { labelKey: 'landing.nav.faq', href: '#faq' }
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
    }
  ];

  readonly pricingPlans: PricingPlan[] = [
    {
      nameKey: 'landing.pricing.plans.launch.name',
      price: '$0',
      priceNoteKey: 'landing.pricing.pricePerMonth',
      taglineKey: 'landing.pricing.plans.launch.tagline',
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
      price: '$79',
      priceNoteKey: 'landing.pricing.pricePerMonth',
      taglineKey: 'landing.pricing.plans.growth.tagline',
      bulletKeys: [
        'landing.pricing.plans.growth.bullets.allLaunch',
        'landing.pricing.plans.growth.bullets.brandable',
        'landing.pricing.plans.growth.bullets.integrations',
        'landing.pricing.plans.growth.bullets.support'
      ]
    },
    {
      nameKey: 'landing.pricing.plans.enterprise.name',
      priceLabelKey: 'landing.pricing.plans.enterprise.priceLabel',
      priceNoteKey: 'landing.pricing.plans.enterprise.priceNote',
      taglineKey: 'landing.pricing.plans.enterprise.tagline',
      bulletKeys: [
        'landing.pricing.plans.enterprise.bullets.onboarding',
        'landing.pricing.plans.enterprise.bullets.analytics',
        'landing.pricing.plans.enterprise.bullets.workflows',
        'landing.pricing.plans.enterprise.bullets.security'
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
        { labelKey: 'landing.footer.columns.resources.links.slack', href: 'mailto:hello@remote-checkin.io?subject=Community%20Invite' }
      ]
    }
  ];

  readonly currentYear = new Date().getFullYear();

  dismissStickyCta(): void {
    this.showStickyCta.set(false);
  }

  ngAfterViewInit(): void {
    if (!this.isBrowser) {
      this.liveProperties.set(this.livePropertyTarget);
      this.selfCheckins.set(this.selfCheckinsTarget);
      this.timeSaved.set(this.timeSavedTarget);
      this.upsellLift.set(this.upsellTarget);
      return;
    }

    this.animateMetric(this.liveProperties, this.livePropertyTarget, 0);
    this.animateMetric(this.selfCheckins, this.selfCheckinsTarget, 0);
    this.animateMetric(this.timeSaved, this.timeSavedTarget, 1);
    this.animateMetric(this.upsellLift, this.upsellTarget, 0);
  }

  private animateMetric(signalRef: ReturnType<typeof signal<number>>, target: number, decimals: number): void {
    if (typeof window === 'undefined' || typeof window.requestAnimationFrame === 'undefined') {
      signalRef.set(parseFloat(target.toFixed(decimals)));
      return;
    }

    const duration = 1200;
    const startTime = performance.now();

    const step = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const value = parseFloat((progress * target).toFixed(decimals));
      signalRef.set(value);

      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        signalRef.set(parseFloat(target.toFixed(decimals)));
      }
    };

    window.requestAnimationFrame(step);
  }
}

