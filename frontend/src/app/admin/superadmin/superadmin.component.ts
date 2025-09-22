import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';

@Component({
    selector: 'app-superadmin',
    standalone: true,
    imports: [CommonModule, RouterOutlet],
    templateUrl: './superadmin.component.html',
    styleUrls: ['./superadmin.component.css']
})
export class SuperadminComponent {

    constructor() { }

}
