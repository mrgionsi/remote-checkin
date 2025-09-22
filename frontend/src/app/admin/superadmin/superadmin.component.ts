import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';

@Component({
    selector: 'app-superadmin',
    standalone: true,
    imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
    templateUrl: './superadmin.component.html',
    styleUrls: ['./superadmin.component.scss']
})
export class SuperadminComponent {

    constructor() { }

}
