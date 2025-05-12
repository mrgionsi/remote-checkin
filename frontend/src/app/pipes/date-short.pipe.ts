import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'dateShort'
})
export class DateShortPipe implements PipeTransform {

  transform(value: string | Date | null | undefined): string {
    if (!value) {
      return '';
    }

    const date = new Date(value);

    // Check if date is valid
    if (isNaN(date.getTime())) {
      return '';
    }

    const day = this.padZero(date.getDate());
    const month = this.padZero(date.getMonth() + 1); // Months are 0-based
    const year = date.getFullYear();

    return `${day}-${month}-${year}`;
  }

  private padZero(n: number): string {
    return n < 10 ? '0' + n : '' + n;
  }
}
