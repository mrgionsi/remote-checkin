import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'documentTypeLabel'
})
export class DocumentTypeLabelPipe implements PipeTransform {

  transform(value: string): string {
    const map: { [key: string]: string } = {
      identity_card: 'Identity card',
      passport: 'Passport',
      driver_license: 'Driver’s License'
      // Add more mappings as needed
    };

    return map[value] || value;
  }

}
