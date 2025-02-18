import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-remote-checkin',
  imports: [],
  templateUrl: './remote-checkin.component.html',
  styleUrl: './remote-checkin.component.scss'
})
export class RemoteCheckinComponent implements OnInit {

  languageCode: string | null = '';
  reservationId: string | null = '';
  constructor(private route: ActivatedRoute, private router: Router) { }

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
}
