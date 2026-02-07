import { NavigationLink } from './header/header.component';

export const LANDING_NAV_LINKS: NavigationLink[] = [
  { labelKey: 'landing.nav.howItWorks', routerLink: '/landing', fragment: 'how-it-works' },
  { labelKey: 'landing.nav.advantages', routerLink: '/landing', fragment: 'advantages' },
  { labelKey: 'landing.nav.features', routerLink: '/landing', fragment: 'features' },
  { labelKey: 'landing.nav.pricing', routerLink: '/pricing' },
  { labelKey: 'landing.nav.selfHost', routerLink: '/landing', fragment: 'self-host' },
  { labelKey: 'landing.nav.faq', routerLink: '/faq' }
];
