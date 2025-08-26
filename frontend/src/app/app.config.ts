import { ApplicationConfig, provideZoneChangeDetection, isDevMode } from '@angular/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { provideClientHydration } from '@angular/platform-browser';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { providePrimeNG } from 'primeng/config';
import Aura from '@primeng/themes/aura';
import { provideHttpClient, withFetch, withInterceptorsFromDi } from '@angular/common/http';
import { TranslocoHttpLoader } from './transloco-loader';
import { provideTransloco } from '@jsverse/transloco';


export const appConfig: ApplicationConfig = {
  providers: [provideAnimationsAsync(), provideHttpClient(withInterceptorsFromDi(), withFetch()),
  providePrimeNG({
    theme: {
      preset: Aura,
      options: {
        cssLayer: {
          name: 'primeng',
          order: 'app-styles, primeng'
        },
        darkModeSelector: false || 'none'
      }
    }
  }),
  provideZoneChangeDetection({ eventCoalescing: true }), provideRouter(routes), provideClientHydration(), provideHttpClient(), provideTransloco({
        config: { 
          availableLangs: ['en', 'es', 'it', 'fr', 'de'],
          defaultLang: 'en',
          // Remove this option if your application doesn't support changing language in runtime.
          reRenderOnLangChange: true,
          prodMode: !isDevMode(),
        },
        loader: TranslocoHttpLoader
      })]
};

