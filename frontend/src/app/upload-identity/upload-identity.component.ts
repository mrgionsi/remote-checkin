// upload-identity.component.ts
import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { FileUploadModule } from 'primeng/fileupload';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { ToastModule } from 'primeng/toast';

@Component({
  selector: 'app-upload-identity',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, FileUploadModule, ButtonModule, CardModule, ToastModule],
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

  constructor(private fb: FormBuilder) {
    this.uploadForm = this.fb.group({
      frontimage: [null, Validators.required],
      backimage: [null, Validators.required],
      selfie: [null, Validators.required]
    });
  }


  onFileSelect(event: any, type: 'frontimage' | 'backimage' | 'selfie') {
    console.log(event)

    const file = event.currentFiles[0];
    console.log(event)
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        if (type === 'frontimage') this.frontPreview = reader.result;
        if (type === 'backimage') this.backPreview = reader.result;
        if (type === 'selfie') this.selfiePreview = reader.result;
      };
      reader.readAsDataURL(file);
      this.uploadForm.patchValue({ [type]: file });

      this.formDataEmitter.emit(this.uploadForm);

    }

  }


}