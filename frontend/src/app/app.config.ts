import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { provideClientHydration } from '@angular/platform-browser';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { providePrimeNG } from 'primeng/config';
import Lara from '@primeng/themes/lara';


export const appConfig: ApplicationConfig = {
  providers: [provideAnimationsAsync(),
  providePrimeNG({
    theme: {
      preset: Lara
    }
  }),
  provideZoneChangeDetection({ eventCoalescing: true }), provideRouter(routes), provideClientHydration()]
};

