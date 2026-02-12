import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';

import { TranslocoService } from '@jsverse/transloco';
import { AdminInfoService } from '../../services/admin-info.service';
import { ChangePasswordComponent } from './change-password.component';

describe('ChangePasswordComponent', () => {
  let component: ChangePasswordComponent;
  let fixture: ComponentFixture<ChangePasswordComponent>;
  let adminInfoService: jasmine.SpyObj<AdminInfoService>;
  let router: jasmine.SpyObj<Router>;

  beforeEach(async () => {
    adminInfoService = jasmine.createSpyObj<AdminInfoService>('AdminInfoService', ['changePassword']);
    router = jasmine.createSpyObj<Router>('Router', ['navigate']);

    await TestBed.configureTestingModule({
      imports: [ChangePasswordComponent],
      providers: [
        { provide: AdminInfoService, useValue: adminInfoService },
        { provide: Router, useValue: router },
        {
          provide: TranslocoService,
          useValue: {
            translate: (key: string) => key,
            getActiveLang: () => 'en',
            langChanges$: of('en'),
            config: {
              reRenderOnLangChange: false
            }
          }
        }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ChangePasswordComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should not submit when form is invalid', () => {
    component.form.patchValue({
      currentPassword: '',
      newPassword: 'weak',
      confirmPassword: 'weak'
    });

    component.onSubmit();

    expect(adminInfoService.changePassword).not.toHaveBeenCalled();
  });

  it('should submit valid form and reset on success', () => {
    adminInfoService.changePassword.and.returnValue(of({ message: 'ok' }));
    component.form.patchValue({
      currentPassword: 'Oldpass123',
      newPassword: 'Newpass123',
      confirmPassword: 'Newpass123'
    });

    component.onSubmit();

    expect(adminInfoService.changePassword).toHaveBeenCalledWith({
      current_password: 'Oldpass123',
      new_password: 'Newpass123',
      confirm_password: 'Newpass123'
    });
    expect(component.successMessage).toBe('change-password-success');
    expect(component.errorMessage).toBe('');
  });

  it('should expose backend error message when available', () => {
    adminInfoService.changePassword.and.returnValue(
      throwError(() => ({ error: { error: 'Current password is incorrect' } }))
    );
    component.form.patchValue({
      currentPassword: 'wrong',
      newPassword: 'Newpass123',
      confirmPassword: 'Newpass123'
    });

    component.onSubmit();

    expect(component.errorMessage).toBe('Current password is incorrect');
    expect(component.successMessage).toBe('');
  });

  it('goBack should navigate to admin dashboard', () => {
    component.goBack();
    expect(router.navigate).toHaveBeenCalledWith(['/admin/dashboard']);
  });
});
