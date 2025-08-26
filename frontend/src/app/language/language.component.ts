import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { TranslocoPipe } from '@jsverse/transloco';

interface Language {
  name: string;
  code: string;
  flag: string;
}

@Component({
  selector: 'app-language',
  imports: [
    CommonModule,
    TranslocoPipe
  ],
  templateUrl: './language.component.html',
  styleUrl: './language.component.scss'
})
export class LanguageComponent {
  languages: Language[] = [
    { name: 'English', code: 'en', flag: '🇬🇧' },
    { name: 'Italian', code: 'it', flag: '🇮🇹' },
    { name: 'Spanish', code: 'es', flag: '🇪🇸' },
    { name: 'French', code: 'fr', flag: '🇫🇷' },
    { name: 'German', code: 'de', flag: '🇩🇪' },
    { name: 'Portuguese', code: 'pt', flag: '🇵🇹' },
    { name: 'Russian', code: 'ru', flag: '🇷🇺' },
    { name: 'Chinese', code: 'zh', flag: '🇨🇳' }
  ];
  private destroy$ = new Subject<void>();

  selectedLanguage: Language = { name: '', code: '', flag: '' };


  constructor(private router: Router, private route: ActivatedRoute) { }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }
  selectLanguage(lang: Language) {
    this.selectedLanguage = lang;

    this.route.params.pipe(takeUntil(this.destroy$)).subscribe(params => {
      const reservationId = params['id']; // Extract the ID

      if (!reservationId) {
        if (this.selectedLanguage) {
          this.router.navigate(['/reservation-check', this.selectedLanguage.code]);
        } else {
          console.error('Both id and code are missing from route params!');
        }
      } else {
        this.router.navigate([`${reservationId}/remote-checkin`, lang.code]); // Navigate safely
      }
    });
  }


}
