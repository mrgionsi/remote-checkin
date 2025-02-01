import { Component } from '@angular/core';
import { MenuItem } from 'primeng/api';
import { MenuModule } from 'primeng/menu';
import { BadgeModule } from 'primeng/badge';
import { RippleModule } from 'primeng/ripple';
import { AvatarModule } from 'primeng/avatar';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { NgModule } from '@angular/core';
import { SidebarModule } from 'primeng/sidebar';
import { ButtonModule } from 'primeng/button';

@Component({
  selector: 'app-admin-home',
  imports: [MenuModule, BadgeModule, RippleModule, AvatarModule, CommonModule,
    RouterOutlet, SidebarModule, ButtonModule],
  templateUrl: './admin-home.component.html',
  styleUrl: './admin-home.component.scss'
})
export class AdminHomeComponent {

  visible: boolean = false;
  menuItems: MenuItem[];

  constructor() {
    this.menuItems = [
      { label: 'Dashboard', icon: 'pi pi-chart-line', routerLink: '/admin/dashboard' },
      { label: 'Add new Reservation', icon: 'pi pi-plus', routerLink: '/admin/create-reservation' },
      { label: 'Settings', icon: 'pi pi-cog', routerLink: '/admin/settings' }
    ];
  }

  toggleSidebar() {
    this.visible = !this.visible;
  }

}