import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-remote-checkin',
  imports: [],
  templateUrl: './remote-checkin.component.html',
  styleUrl: './remote-checkin.component.scss'
})
export class RemoteCheckinComponent implements OnInit {

  languageCode: string | null = '';

  constructor(private route: ActivatedRoute) { }

  ngOnInit() {
    this.languageCode = this.route.snapshot.paramMap.get('code');
  }
}
