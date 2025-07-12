import { Component } from '@angular/core';
import { MenuItem } from 'primeng/api';
import { MenuModule } from 'primeng/menu';
import { BadgeModule } from 'primeng/badge';
import { RippleModule } from 'primeng/ripple';
import { AvatarModule } from 'primeng/avatar';
import { CommonModule } from '@angular/common';
import { Router, RouterOutlet } from '@angular/router';
import { SidebarModule } from 'primeng/sidebar';
import { ButtonModule } from 'primeng/button';
import { AuthService } from '../../services/auth.service'; // <--- aggiungi import

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

  constructor(public router: Router, private authService: AuthService) {
    this.menuItems = [
      { label: 'Dashboard', icon: 'pi pi-chart-line', routerLink: '/admin/dashboard' },
      { label: 'Add new Reservation', icon: 'pi pi-plus', routerLink: '/admin/create-reservation' },
      { label: 'Rooms', icon: 'pi pi-warehouse', routerLink: '/admin/rooms' },
      { label: 'Settings', icon: 'pi pi-cog', routerLink: '/admin/settings' }
    ];
  }

  toggleSidebar() {
    this.visible = !this.visible;
  }

  ngOnInit() {
    if (!this.authService.isLoggedIn()) {
      this.router.navigate(['/admin/login']);
      return;
    }
    if (this.authService.isSuperAdmin()) {
      this.menuItems.push({
        label: 'Superadmin Panel',
        icon: 'pi pi-shield',
        routerLink: '/admin/superadmin'
      });
    }
  }

  isLoginPage(): boolean {
    return this.router.url === '/admin/login';
  }

}