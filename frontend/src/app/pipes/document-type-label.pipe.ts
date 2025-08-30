import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'documentTypeLabel',
  standalone: true
})
export class DocumentTypeLabelPipe implements PipeTransform {
  transform(value: string): string {
    switch (value) {
      case 'identity_card':
        return 'identity-card-label';
      case 'driver_license':
        return 'driver-license-label';
      case 'passport':
        return 'passport-label';
      default:
        return value;
    }
  }
}
