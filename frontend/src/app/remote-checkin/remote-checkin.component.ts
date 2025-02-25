import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { FormGroup, FormBuilder, Validators, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { DatePickerModule } from 'primeng/datepicker';
import { CardModule } from 'primeng/card';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { InputGroupModule } from 'primeng/inputgroup';
import { InputGroupAddonModule } from 'primeng/inputgroupaddon';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select'; // Import PrimeNG Select
import { StepperModule } from 'primeng/stepper';

@Component({
  selector: 'app-remote-checkin',
  standalone: true,
  imports: [StepperModule,
    DatePickerModule, InputGroupAddonModule, InputTextModule, CardModule,
    FormsModule, ReactiveFormsModule, InputGroupModule, ButtonModule,
    CommonModule, SelectModule
  ],
  templateUrl: './remote-checkin.component.html',
  styleUrl: './remote-checkin.component.scss',
  providers: [MessageService]
})
export class RemoteCheckinComponent implements OnInit {
  clientForm: FormGroup;
  documentTypes = [
    { label: 'Identity Card', value: 'identity_card' },
    { label: 'Driver License', value: 'driver_license' },
    { label: 'Passport', value: 'passport' }
  ];

  languageCode: string | null = '';
  reservationId: string | null = '';

  constructor(private route: ActivatedRoute, private router: Router, private fb: FormBuilder) {
    this.clientForm = this.fb.group({
      name: ['', Validators.required],
      surname: ['', Validators.required],
      birthday: ['', Validators.required],
      street: ['', Validators.required],
      number_city: ['', Validators.required],
      city: ['', Validators.required],
      province: ['', Validators.required],
      cap: ['', [Validators.required, Validators.pattern('^[0-9]{5}$')]],
      telephone: ['', [Validators.required, Validators.pattern('^[0-9]+$')]],
      document_type: ['', Validators.required],  // New field
      document_number: ['', Validators.required],
      cf: ['', [Validators.required, Validators.pattern('^[A-Z0-9]{16}$')]],
    });
  }

  ngOnInit() {
    this.languageCode = this.route.snapshot.paramMap.get('code');
    this.route.params.subscribe(params => {
      if (!params['id']) {
        this.router.navigate(['/reservation-check', params['code']]);
      } else {
        this.reservationId = this.route.snapshot.paramMap.get('id');
      }
    });
  }

  onSubmit() {
    if (this.clientForm.valid) {
      console.log('Form Submitted', this.clientForm.value);
    }
  }
}
