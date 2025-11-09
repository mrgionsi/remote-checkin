import { CommonModule, isPlatformBrowser } from '@angular/common';
import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  Inject,
  OnDestroy,
  ViewChild,
  signal
} from '@angular/core';
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

interface HeroStat {
  target: number;
  decimals?: number;
  valuePrefix?: string;
  valueSuffix?: string;
  valueSuffixKey?: string;
  labelKey: string;
  displayValue: number;
  className?: string;
  format: string;
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
export class LandingComponent implements AfterViewInit, OnDestroy {
  @ViewChild('heroStatsSection') private heroStatsSection?: ElementRef<HTMLElement>;

  readonly showStickyCta = signal(true);

  private heroStatsAnimated = false;
  private observer?: IntersectionObserver;
  private readonly isBrowser: boolean;

  constructor(
    private readonly cdr: ChangeDetectorRef,
    @Inject(PLATFORM_ID) platformId: object
  ) {
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

  readonly heroStats: HeroStat[] = [
    {
      target: 48,
      labelKey: 'landing.hero.stats.properties',
      displayValue: 0,
      format: '1.0-0'
    },
    {
      target: 92,
      valueSuffix: '%',
      labelKey: 'landing.hero.stats.completion',
      displayValue: 0,
      className: 'tile--primary',
      format: '1.0-0'
    },
    {
      target: 1.8,
      decimals: 1,
      valueSuffixKey: 'landing.hero.stats.timeSavedSuffix',
      labelKey: 'landing.hero.stats.timeSaved',
      displayValue: 0,
      className: 'tile--secondary',
      format: '1.0-1'
    },
    {
      target: 36,
      valuePrefix: '+',
      valueSuffix: '%',
      labelKey: 'landing.hero.stats.upsell',
      displayValue: 0,
      className: 'tile--accent',
      format: '1.0-0'
    }
  ];

  readonly currentYear = new Date().getFullYear();

  ngAfterViewInit(): void {
    if (!this.heroStatsSection || !this.isBrowser || typeof IntersectionObserver === 'undefined') {
      return;
    }

    this.observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting && !this.heroStatsAnimated) {
            this.heroStatsAnimated = true;
            this.animateHeroStats();
            this.observer?.disconnect();
          }
        });
      },
      { threshold: 0.4 }
    );

    this.observer.observe(this.heroStatsSection.nativeElement);
  }

  dismissStickyCta(): void {
    this.showStickyCta.set(false);
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
  }

  private animateHeroStats(): void {
    if (!this.isBrowser || typeof requestAnimationFrame === 'undefined') {
      return;
    }

    const duration = 1400;
    const startTime = performance.now();

    const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);

    const step = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = easeOutCubic(progress);

      this.heroStats.forEach(stat => {
        const value = stat.target * eased;
        const decimals = stat.decimals ?? 0;
        stat.displayValue = parseFloat(value.toFixed(decimals));
      });

      this.cdr.markForCheck();

      if (progress < 1) {
        requestAnimationFrame(step);
      }
    };

    requestAnimationFrame(step);
  }
}

