import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'documentTypeLabel'
})
export class DocumentTypeLabelPipe implements PipeTransform {

  transform(value: unknown, ...args: unknown[]): unknown {
    return null;
  }

}
