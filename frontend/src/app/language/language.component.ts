import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { Router } from '@angular/router';

interface Language {
  name: string;
  code: string;
  flag: string;
}

@Component({
  selector: 'app-language',
  imports: [CommonModule],
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

  selectedLanguage: Language = this.languages[1]; // Default to Italian


  constructor(private router: Router) { }

  selectLanguage(lang: Language) {
    this.selectedLanguage = lang;
    this.router.navigate(['/remote-checkin', lang.code]); // Navigate to new page
  }

}
