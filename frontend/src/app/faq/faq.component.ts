import { CommonModule } from '@angular/common';
import { AfterViewInit, ChangeDetectionStrategy, ChangeDetectorRef, Component } from '@angular/core';
import { RouterModule } from '@angular/router';
import {
  animate,
  style,
  transition,
  trigger
} from '@angular/animations';
import { TranslocoPipe } from '@jsverse/transloco';
import { HeaderComponent } from '../shared/header/header.component';
import { LANDING_NAV_LINKS } from '../shared/navigation';

interface FAQCategory {
  id: string;
  titleKey: string;
  icon: string;
  items: FAQItem[];
}

interface FAQItem {
  questionKey: string;
  answerKey: string;
  expanded: boolean;
}

interface FAQCategoryWithItems extends Omit<FAQCategory, 'items'> {
  items: FAQItem[];
}


@Component({
  selector: 'app-faq',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslocoPipe, HeaderComponent],
  templateUrl: './faq.component.html',
  styleUrl: './faq.component.scss',
  animations: [
    trigger('pageFade', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('500ms ease-out', style({ opacity: 1 }))
      ])
    ]),
    trigger('itemExpand', [
      transition(':enter', [
        style({ height: 0, opacity: 0 }),
        animate('300ms ease-out', style({ height: '*', opacity: 1 }))
      ]),
      transition(':leave', [
        animate('300ms ease-in', style({ height: 0, opacity: 0 }))
      ])
    ])
  ],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class FAQComponent implements AfterViewInit {
  readonly navLinks = LANDING_NAV_LINKS;

  constructor(
    private readonly cdr: ChangeDetectorRef
  ) {}

  readonly categories: FAQCategoryWithItems[] = [
    {
      id: 'getting-started',
      titleKey: 'faq.categories.gettingStarted.title',
      icon: 'pi pi-rocket',
      items: [
        { questionKey: 'faq.categories.gettingStarted.items.setup.question', answerKey: 'faq.categories.gettingStarted.items.setup.answer', expanded: false },
        { questionKey: 'faq.categories.gettingStarted.items.onboarding.question', answerKey: 'faq.categories.gettingStarted.items.onboarding.answer', expanded: false },
        { questionKey: 'faq.categories.gettingStarted.items.timeToLaunch.question', answerKey: 'faq.categories.gettingStarted.items.timeToLaunch.answer', expanded: false },
        { questionKey: 'faq.categories.gettingStarted.items.training.question', answerKey: 'faq.categories.gettingStarted.items.training.answer', expanded: false }
      ]
    },
    {
      id: 'features',
      titleKey: 'faq.categories.features.title',
      icon: 'pi pi-star',
      items: [
        { questionKey: 'faq.categories.features.items.documents.question', answerKey: 'faq.categories.features.items.documents.answer', expanded: false },
        { questionKey: 'faq.categories.features.items.languages.question', answerKey: 'faq.categories.features.items.languages.answer', expanded: false },
        { questionKey: 'faq.categories.features.items.mobile.question', answerKey: 'faq.categories.features.items.mobile.answer', expanded: false },
        { questionKey: 'faq.categories.features.items.notifications.question', answerKey: 'faq.categories.features.items.notifications.answer', expanded: false },
        { questionKey: 'faq.categories.features.items.customization.question', answerKey: 'faq.categories.features.items.customization.answer', expanded: false }
      ]
    },
    {
      id: 'pricing',
      titleKey: 'faq.categories.pricing.title',
      icon: 'pi pi-dollar',
      items: [
        { questionKey: 'faq.categories.pricing.items.plans.question', answerKey: 'faq.categories.pricing.items.plans.answer', expanded: false },
        { questionKey: 'faq.categories.pricing.items.billing.question', answerKey: 'faq.categories.pricing.items.billing.answer', expanded: false },
        { questionKey: 'faq.categories.pricing.items.cancellation.question', answerKey: 'faq.categories.pricing.items.cancellation.answer', expanded: false },
        { questionKey: 'faq.categories.pricing.items.trial.question', answerKey: 'faq.categories.pricing.items.trial.answer', expanded: false },
        { questionKey: 'faq.categories.pricing.items.refund.question', answerKey: 'faq.categories.pricing.items.refund.answer', expanded: false }
      ]
    },
    {
      id: 'technical',
      titleKey: 'faq.categories.technical.title',
      icon: 'pi pi-cog',
      items: [
        { questionKey: 'faq.categories.technical.items.integration.question', answerKey: 'faq.categories.technical.items.integration.answer', expanded: false },
        { questionKey: 'faq.categories.technical.items.api.question', answerKey: 'faq.categories.technical.items.api.answer', expanded: false },
        { questionKey: 'faq.categories.technical.items.selfHost.question', answerKey: 'faq.categories.technical.items.selfHost.answer', expanded: false },
        { questionKey: 'faq.categories.technical.items.requirements.question', answerKey: 'faq.categories.technical.items.requirements.answer', expanded: false },
        { questionKey: 'faq.categories.technical.items.uptime.question', answerKey: 'faq.categories.technical.items.uptime.answer', expanded: false }
      ]
    },
    {
      id: 'compliance',
      titleKey: 'faq.categories.compliance.title',
      icon: 'pi pi-shield',
      items: [
        { questionKey: 'faq.categories.compliance.items.gdpr.question', answerKey: 'faq.categories.compliance.items.gdpr.answer', expanded: false },
        { questionKey: 'faq.categories.compliance.items.portaleAlloggi.question', answerKey: 'faq.categories.compliance.items.portaleAlloggi.answer', expanded: false },
        { questionKey: 'faq.categories.compliance.items.dataRetention.question', answerKey: 'faq.categories.compliance.items.dataRetention.answer', expanded: false },
        { questionKey: 'faq.categories.compliance.items.audit.question', answerKey: 'faq.categories.compliance.items.audit.answer', expanded: false },
        { questionKey: 'faq.categories.compliance.items.regions.question', answerKey: 'faq.categories.compliance.items.regions.answer', expanded: false }
      ]
    },
    {
      id: 'support',
      titleKey: 'faq.categories.support.title',
      icon: 'pi pi-question-circle',
      items: [
        { questionKey: 'faq.categories.support.items.contact.question', answerKey: 'faq.categories.support.items.contact.answer', expanded: false },
        { questionKey: 'faq.categories.support.items.responseTime.question', answerKey: 'faq.categories.support.items.responseTime.answer', expanded: false },
        { questionKey: 'faq.categories.support.items.documentation.question', answerKey: 'faq.categories.support.items.documentation.answer', expanded: false },
        { questionKey: 'faq.categories.support.items.community.question', answerKey: 'faq.categories.support.items.community.answer', expanded: false }
      ]
    }
  ];

  readonly currentYear = new Date().getFullYear();

  toggleItem(categoryIndex: number, itemIndex: number): void {
    const item = this.categories[categoryIndex].items[itemIndex];
    item.expanded = !item.expanded;
    this.cdr.markForCheck();
  }

  ngAfterViewInit(): void {
    // Component initialization if needed
  }
}
