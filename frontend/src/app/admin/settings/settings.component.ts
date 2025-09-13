import { Component, Inject, OnInit, PLATFORM_ID } from '@angular/core';
import { DropdownModule } from 'primeng/dropdown';
import { TranslocoPipe, TranslocoService } from '@jsverse/transloco';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { isPlatformBrowser, CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { ToastModule } from 'primeng/toast';
import { CheckboxModule } from 'primeng/checkbox';
import { PasswordModule } from 'primeng/password';
import { MessageService } from 'primeng/api';
import { EmailConfig, EmailConfigService, EmailProviderPreset } from '../../services/email-config.service';
import { PortaleAlloggiService, PortaleAlloggiConfig } from '../../services/portale-alloggi.service';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [DropdownModule, FormsModule, ReactiveFormsModule, TranslocoPipe, CommonModule, ButtonModule, InputTextModule, ToastModule, CheckboxModule, PasswordModule],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss',
  providers: [MessageService]
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

  // Email settings
  emailForm: FormGroup;
  presets: { key: string; label: string }[] = [];
  presetMap: { [key: string]: EmailProviderPreset } = {};
  provider_config: boolean = false;

  // Portale Alloggi settings
  portaleForm: FormGroup;
  testingPortale = false;
  savingPortale = false;

  constructor(
    private readonly translocoService: TranslocoService,
    @Inject(PLATFORM_ID) private readonly platformId: Object,
    private fb: FormBuilder,
    private emailConfigService: EmailConfigService,
    private portaleAlloggiService: PortaleAlloggiService,
    private messageService: MessageService,
    private http: HttpClient
  ) {
    this.emailForm = this.fb.group({
      preset: [''], // Add preset as a form control
      mail_server: ['', Validators.required],
      mail_port: [587, [Validators.required]],
      mail_use_tls: [true],
      mail_use_ssl: [false],
      mail_username: ['', Validators.required],
      mail_password: ['', Validators.required],
      mail_default_sender_name: [''],
      mail_default_sender_email: ['', [Validators.required, Validators.email]],
      provider_type: ['smtp', Validators.required],
      provider_config: this.fb.group({
        domain: [''],
        api_key: ['']
      })
    });

    // Initialize Portale Alloggi form
    this.portaleForm = this.fb.group({
      portale_username: [''],
      portale_password: [''],
      portale_wskey: ['']
    });
  }

  ngOnInit() {
    const stored = isPlatformBrowser(this.platformId) ? localStorage.getItem('appLang') : null;
    this.selectedLang = stored || 'en';
    this.translocoService.setActiveLang(this.selectedLang);

    // Load email settings
    this.loadEmailPresets();
    this.loadEmailConfig();

    // Load Portale Alloggi settings
    this.loadPortaleConfig();
  }



  saveLanguage() {
    if (isPlatformBrowser(this.platformId)) {
      localStorage.setItem('appLang', this.selectedLang);
    } this.translocoService.setActiveLang(this.selectedLang); // Cambia la lingua dell'app
    this.saved = true;
  }

  // Email settings methods
  loadEmailPresets(): void {
    this.emailConfigService.getEmailPresets().subscribe({
      next: (presets) => {
        this.presetMap = presets;
        this.presets = Object.keys(presets).map(k => ({ key: k, label: presets[k].name }));
      }
    });
  }

  applyEmailPreset(key: string): void {
    const preset = this.presetMap[key];
    if (!preset) return;

    this.emailForm.patchValue({
      preset: key, // Update the preset form control
      mail_server: preset.mail_server,
      mail_port: preset.mail_port,
      mail_use_tls: preset.mail_use_tls,
      mail_use_ssl: preset.mail_use_ssl,
      provider_type: preset.provider_type ?? 'smtp'
    });
    this.messageService.add({
      severity: 'info',
      summary: this.translocoService.translate('settings.presetApplied'),
      detail: this.translocoService.translate('settings.presetInstructions', { instructions: preset.instructions })
    });
  }

  loadEmailConfig(): void {
    // Load email config with decrypted password for editing
    this.emailConfigService.getEmailConfig(true).subscribe({
      next: (config) => {
        if (!config) return;

        this.emailForm.patchValue({
          mail_server: config.mail_server,
          mail_port: config.mail_port,
          mail_use_tls: config.mail_use_tls,
          mail_use_ssl: config.mail_use_ssl,
          mail_username: config.mail_username,
          mail_password: config.mail_password,
          mail_default_sender_name: config.mail_default_sender_name,
          mail_default_sender_email: config.mail_default_sender_email,
          provider_type: config.provider_type || 'smtp'
        });

        // provider_config is optional JSON
        if (config.provider_config) {
          this.emailForm.get('provider_config')?.patchValue(config.provider_config);
        }

        // Auto-select the corresponding preset based on current configuration
        this.selectMatchingPreset(config);
      },
      error: () => { }
    });
  }

  saveEmailConfig(): void {
    if (this.emailForm.invalid) {
      this.emailForm.markAllAsTouched();
      this.messageService.add({
        severity: 'warn',
        summary: this.translocoService.translate('settings.validation'),
        detail: this.translocoService.translate('settings.fillRequiredFields')
      });
      return;
    }
    const payload: EmailConfig = {
      ...(this.emailForm.value as any),
      is_active: true
    };
    this.emailConfigService.saveEmailConfig(payload).subscribe({
      next: () => this.messageService.add({
        severity: 'success',
        summary: this.translocoService.translate('settings.saved'),
        detail: this.translocoService.translate('settings.emailConfigSaved')
      }),
      error: (e) => this.messageService.add({
        severity: 'error',
        summary: this.translocoService.translate('settings.error'),
        detail: e?.error?.error || this.translocoService.translate('settings.saveFailed')
      })
    });
  }

  testEmailConfig(): void {
    const to = this.emailForm.get('mail_username')?.value || this.emailForm.get('mail_default_sender_email')?.value;
    if (!to) {
      this.messageService.add({
        severity: 'warn',
        summary: this.translocoService.translate('settings.testEmail'),
        detail: this.translocoService.translate('settings.setTestRecipientFirst')
      });
      return;
    }
    this.emailConfigService.testEmailConfig(to).subscribe({
      next: (res) => {
        if (res.status === 'success' || (res as any).message?.includes('success')) {
          this.messageService.add({
            severity: 'success',
            summary: this.translocoService.translate('settings.testEmail'),
            detail: this.translocoService.translate('settings.testEmailSentSuccessfully')
          });
        } else {
          this.messageService.add({
            severity: 'warn',
            summary: this.translocoService.translate('settings.testEmail'),
            detail: this.translocoService.translate('settings.testEmailFailed')
          });
        }
      },
      error: (e) => this.messageService.add({
        severity: 'error',
        summary: this.translocoService.translate('settings.testEmail'),
        detail: e?.error?.error || this.translocoService.translate('settings.testFailed')
      })
    });
  }



  selectMatchingPreset(config: any): void {
    // Find the preset that matches the current configuration
    for (const [key, preset] of Object.entries(this.presetMap)) {
      if (this.configMatchesPreset(config, preset)) {
        this.emailForm.patchValue({ preset: key });
        return;
      }
    }
    // If no preset matches, set to empty (custom configuration)
    this.emailForm.patchValue({ preset: '' });
  }

  configMatchesPreset(config: any, preset: EmailProviderPreset): boolean {
    // Check if the configuration matches a preset
    return config.mail_server === preset.mail_server &&
      config.mail_port === preset.mail_port &&
      config.mail_use_tls === preset.mail_use_tls &&
      config.mail_use_ssl === preset.mail_use_ssl &&
      (config.provider_type === preset.provider_type ||
        (config.provider_type === 'smtp' && !preset.provider_type));
  }

  // Portale Alloggi methods
  loadPortaleConfig(): void {
    this.portaleAlloggiService.getConfig().subscribe({
      next: (response) => {
        if (response.config) {
          this.portaleForm.patchValue({
            portale_username: response.config.portale_username || '',
            portale_password: '', // Don't load password for security - user needs to re-enter
            portale_wskey: response.config.portale_wskey || ''
          });

          // Show info message if password exists but is masked
          if (response.config.portale_password === '***') {
            this.messageService.add({
              severity: 'info',
              summary: 'Info',
              detail: this.translocoService.translate('portale-alloggi-password-configured-message')
            });
          }
        }
      },
      error: (error) => {
        console.error('Error loading Portale Alloggi config:', error);
        // Don't show error message as this might be the first time setting up
      }
    });
  }

  savePortaleConfig(): void {
    if (this.portaleForm.valid) {
      this.savingPortale = true;

      const formValue = this.portaleForm.value;

      // Only include password if it's not empty (to avoid overwriting existing password)
      const config: PortaleAlloggiConfig = {
        portale_username: formValue.portale_username,
        portale_wskey: formValue.portale_wskey,
        portale_password: formValue.portale_password || '' // Include empty string if no password provided
      };

      this.portaleAlloggiService.saveConfig(config).subscribe({
        next: (response) => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: this.translocoService.translate('portale-config-saved')
          });
          this.savingPortale = false;
        },
        error: (error) => {
          console.error('Error saving Portale Alloggi config:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.error?.error || 'Failed to save Portale Alloggi configuration'
          });
          this.savingPortale = false;
        }
      });
    } else {
      this.messageService.add({
        severity: 'warn',
        summary: 'Warning',
        detail: 'Please fill in all required fields'
      });
    }
  }

  testPortaleConnection(): void {
    this.testingPortale = true;

    this.portaleAlloggiService.testConnection().subscribe({
      next: (response) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: this.translocoService.translate('portale-connection-success')
        });
        this.testingPortale = false;
      },
      error: (error) => {
        console.error('Error testing Portale Alloggi connection:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: this.translocoService.translate('portale-connection-failed')
        });
        this.testingPortale = false;
      }
    });
  }
}
