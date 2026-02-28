// upload-identity.component.ts
import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { FileUploadModule } from 'primeng/fileupload';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { ToastModule } from 'primeng/toast';
import { ProgressBarModule } from 'primeng/progressbar';
import { TranslocoPipe, TranslocoService } from '@jsverse/transloco';

@Component({
  selector: 'app-upload-identity',
  standalone: true,
  imports: [CommonModule, TranslocoPipe, FormsModule, ReactiveFormsModule, FileUploadModule, ButtonModule, CardModule, ToastModule, ProgressBarModule],
  templateUrl: './upload-identity.component.html',
  styleUrl: './upload-identity.component.scss',
  providers: [MessageService]
})
export class UploadIdentityComponent {
  uploadForm: FormGroup;
  frontPreview: string | ArrayBuffer | null = null;
  backPreview: string | ArrayBuffer | null = null;
  selfiePreview: string | ArrayBuffer | null = null;
  @Output() formDataEmitter = new EventEmitter<FormGroup>();

  constructor(
    private fb: FormBuilder,
    private messageService: MessageService,
    private readonly translocoService: TranslocoService
  ) {
    this.uploadForm = this.fb.group({
      frontimage: [null, Validators.required],
      backimage: [null, Validators.required],
      selfie: [null, Validators.required]
    });
  }

  onFileSelect(event: any, type: 'frontimage' | 'backimage' | 'selfie') {
    const file = event.currentFiles[0];

    if (file) {
      // Validate file size (5MB max)
      if (file.size > 5000000) {
        this.messageService.add({
          severity: 'error',
          summary: this.translocoService.translate('error'),
          detail: this.translocoService.translate('upload-file-too-large')
        });
        return;
      }

      // Validate file type
      const allowedTypes = ['image/jpeg', 'image/png'];
      if (!allowedTypes.includes(file.type)) {
        this.messageService.add({
          severity: 'error',
          summary: this.translocoService.translate('error'),
          detail: this.translocoService.translate('upload-invalid-file-type')
        });
        return;
      }

      const reader = new FileReader();
      reader.onload = () => {
        if (type === 'frontimage') this.frontPreview = reader.result;
        if (type === 'backimage') this.backPreview = reader.result;
        if (type === 'selfie') this.selfiePreview = reader.result;
      };
      reader.readAsDataURL(file);

      this.uploadForm.patchValue({ [type]: file });
      this.uploadForm.get(type)?.setErrors(null);
      this.formDataEmitter.emit(this.uploadForm);

      // Show success message
      this.messageService.add({
        severity: 'success',
        summary: this.translocoService.translate('success'),
        detail: this.translocoService.translate('upload-image-uploaded-success')
      });
    }
  }

  removeImage(type: 'frontimage' | 'backimage' | 'selfie') {
    this.uploadForm.patchValue({ [type]: null });

    // Clear preview
    if (type === 'frontimage') this.frontPreview = null;
    if (type === 'backimage') this.backPreview = null;
    if (type === 'selfie') this.selfiePreview = null;

    this.formDataEmitter.emit(this.uploadForm);

    this.messageService.add({
      severity: 'info',
      summary: this.translocoService.translate('success'),
      detail: this.translocoService.translate('upload-image-removed')
    });
  }

  getImagePreview(type: 'frontimage' | 'backimage' | 'selfie'): string | ArrayBuffer | null {
    const file = this.uploadForm.get(type)?.value;
    if (file && file.objectURL) {
      return file.objectURL;
    }

    // Fallback to stored preview
    if (type === 'frontimage') return this.frontPreview;
    if (type === 'backimage') return this.backPreview;
    if (type === 'selfie') return this.selfiePreview;

    return null;
  }

  getUploadProgress(): number {
    let count = 0;
    if (this.uploadForm.get('frontimage')?.value) count++;
    if (this.uploadForm.get('backimage')?.value) count++;
    if (this.uploadForm.get('selfie')?.value) count++;
    return count;
  }
}
