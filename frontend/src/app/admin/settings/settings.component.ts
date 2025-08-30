import { Component, Inject, OnInit, PLATFORM_ID } from '@angular/core';
import { DropdownModule } from 'primeng/dropdown';
import { TranslocoPipe, TranslocoService } from '@jsverse/transloco';
import { FormsModule } from '@angular/forms';
import { isPlatformBrowser, CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [DropdownModule, FormsModule, TranslocoPipe, CommonModule, ButtonModule],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss'
})
export class SettingsComponent implements OnInit {
  languages = [
    { label: 'English', value: 'en' },
    { label: 'Italiano', value: 'it' },
    { label: 'Español', value: 'es' },
    { label: 'Français', value: 'fr' },
    { label: 'Deutsch', value: 'de' }
  ];
  selectedLang = 'en';
  saved = false;

  constructor(private translocoService: TranslocoService, @Inject(PLATFORM_ID) private platformId: Object) { }

  ngOnInit() {
    const stored = isPlatformBrowser(this.platformId) ? localStorage.getItem('appLang') : null;
    this.selectedLang = stored || 'en';
    this.translocoService.setActiveLang(this.selectedLang);
  }



  saveLanguage() {
    if (isPlatformBrowser(this.platformId)) {
      localStorage.setItem('appLang', this.selectedLang);
    } this.translocoService.setActiveLang(this.selectedLang); // Cambia la lingua dell'app
    this.saved = true;
  }
}
