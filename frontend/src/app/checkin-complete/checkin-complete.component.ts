import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { TranslocoPipe } from '@jsverse/transloco';

@Component({
  selector: 'app-checkin-complete',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslocoPipe],
  templateUrl: './checkin-complete.component.html',
  styleUrl: './checkin-complete.component.scss'
})
export class CheckinCompleteComponent {
  readonly reservationId: string | null;

  constructor(private readonly route: ActivatedRoute) {
    this.reservationId = this.route.snapshot.paramMap.get('id');
  }
}
