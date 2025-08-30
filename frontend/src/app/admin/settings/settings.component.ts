import { Component } from '@angular/core';
import { DropdownModule } from 'primeng/dropdown';
import { TranslocoPipe, TranslocoService } from '@jsverse/transloco';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [DropdownModule, FormsModule, TranslocoPipe, CommonModule, ButtonModule],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss'
})
export class SettingsComponent {
  languages = [
    { label: 'English', value: 'en' },
    { label: 'Italiano', value: 'it' },
    { label: 'Español', value: 'es' },
    { label: 'Français', value: 'fr' },
    { label: 'Deutsch', value: 'de' }
  ];
  selectedLang = localStorage.getItem('appLang') || 'en';
  saved = false;

  constructor(private translocoService: TranslocoService) { }

  saveLanguage() {
    localStorage.setItem('appLang', this.selectedLang);
    this.translocoService.setActiveLang(this.selectedLang); // Cambia la lingua dell'app
    this.saved = true;
  }
}
