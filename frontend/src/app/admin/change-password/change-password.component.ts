import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { AbstractControl, FormBuilder, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { TranslocoPipe, TranslocoService } from '@jsverse/transloco';
import { AdminInfoService } from '../../services/admin-info.service';

function passwordStrengthValidator(control: AbstractControl): ValidationErrors | null {
  const value = String(control.value || '');
  if (!value) {
    return null;
  }
  const hasLetter = /[A-Za-z]/.test(value);
  const hasDigit = /\d/.test(value);
  if (value.length < 8 || !hasLetter || !hasDigit) {
    return { weakPassword: true };
  }
  return null;
}

function passwordsMatchValidator(group: AbstractControl): ValidationErrors | null {
  const newPassword = group.get('newPassword')?.value;
  const confirmPassword = group.get('confirmPassword')?.value;
  if (!newPassword || !confirmPassword) {
    return null;
  }
  return newPassword === confirmPassword ? null : { passwordMismatch: true };
}

@Component({
  selector: 'app-change-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, InputTextModule, ButtonModule, TranslocoPipe],
  templateUrl: './change-password.component.html',
  styleUrl: './change-password.component.scss'
})
export class ChangePasswordComponent {
  saving = false;
  successMessage = '';
  errorMessage = '';

  readonly form;

  constructor(
    private readonly fb: FormBuilder,
    private readonly adminInfoService: AdminInfoService,
    private readonly translocoService: TranslocoService,
    private readonly router: Router
  ) {
    this.form = this.fb.group({
      currentPassword: ['', [Validators.required]],
      newPassword: ['', [Validators.required, passwordStrengthValidator]],
      confirmPassword: ['', [Validators.required]]
    }, { validators: passwordsMatchValidator });
  }

  onSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const { currentPassword, newPassword, confirmPassword } = this.form.getRawValue();
    if (!currentPassword || !newPassword || !confirmPassword) {
      return;
    }

    this.errorMessage = '';
    this.successMessage = '';
    this.saving = true;

    this.adminInfoService.changePassword({
      current_password: currentPassword,
      new_password: newPassword,
      confirm_password: confirmPassword
    }).subscribe({
      next: () => {
        this.saving = false;
        this.successMessage = this.translocoService.translate('change-password-success');
        this.form.reset();
      },
      error: (error) => {
        this.saving = false;
        const backendMessage = String(error?.error?.error || '').trim();
        if (backendMessage) {
          this.errorMessage = backendMessage;
          return;
        }
        this.errorMessage = this.translocoService.translate('change-password-error');
      }
    });
  }

  goBack(): void {
    this.router.navigate(['/admin/dashboard']);
  }

  hasControlError(controlName: 'currentPassword' | 'newPassword' | 'confirmPassword', errorKey: string): boolean {
    const control = this.form.get(controlName);
    return !!(control?.touched && control?.errors?.[errorKey]);
  }
}
