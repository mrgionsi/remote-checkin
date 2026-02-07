import { CommonModule, isPlatformBrowser } from '@angular/common';
import { AfterViewInit, ChangeDetectionStrategy, ChangeDetectorRef, Component, Inject, Input, PLATFORM_ID } from '@angular/core';
import { RouterModule } from '@angular/router';
import { TranslocoPipe, TranslocoService } from '@jsverse/transloco';

export interface NavigationLink {
  labelKey: string;
  href?: string;
  routerLink?: string;
  fragment?: string;
}

export interface LanguageOption {
  code: string;
  label: string;
}

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslocoPipe],
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class HeaderComponent implements AfterViewInit {
  @Input() navLinks: NavigationLink[] = [];
  @Input() showLanguageMenu: boolean = true;
  @Input() showCta: boolean = true;
  @Input() ctaRouterLink: string = '/pricing';
  @Input() ctaLabelKey: string = 'landing.actions.claimSpot';
  @Input() brandRouterLink: string | null = null;

  private readonly supportedLanguages = ['en', 'it', 'es'];
  private readonly isBrowser: boolean;

  constructor(
    @Inject(PLATFORM_ID) platformId: object,
    private readonly transloco: TranslocoService,
    private readonly cdr: ChangeDetectorRef
  ) {
    this.isBrowser = isPlatformBrowser(platformId);
  }

  get activeLang(): string {
    return this.transloco.getActiveLang();
  }

  readonly languageOptions: LanguageOption[] = [
    { code: 'en', label: 'English' },
    { code: 'it', label: 'Italiano' },
    { code: 'es', label: 'Español' }
  ];

  changeLanguage(code: string): void {
    if (!this.supportedLanguages.includes(code)) {
      return;
    }
    this.transloco.setActiveLang(code);
    if (this.isBrowser) {
      localStorage.setItem('remote-checkin-lang', code);
    }
    this.cdr.markForCheck();
  }

  ngAfterViewInit(): void {
    if (this.isBrowser) {
      this.detectBrowserLanguage();
    }
  }

  private detectBrowserLanguage(): void {
    const stored = localStorage.getItem('remote-checkin-lang');
    if (stored && this.supportedLanguages.includes(stored)) {
      this.changeLanguage(stored);
      return;
    }

    const browserLang = navigator.language?.split('-')[0]?.toLowerCase() || 'en';
    const langToUse = this.supportedLanguages.includes(browserLang) ? browserLang : 'en';

    this.changeLanguage(langToUse);
  }
}
