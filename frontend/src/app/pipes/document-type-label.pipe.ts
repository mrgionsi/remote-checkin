import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'documentTypeLabel',
  standalone: true
})
export class DocumentTypeLabelPipe implements PipeTransform {
  private readonly types = [
    { label: 'Identity Card', value: 'identity_card' },
    { label: 'Driver License', value: 'driver_license' },
    { label: 'Passport', value: 'passport' }
  ];

  transform(value: string): string {
    const found = this.types.find(t => t.value === value);
    return found ? found.label : value;
  }
}
