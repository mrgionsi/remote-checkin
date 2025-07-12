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
import { DropdownModule } from 'primeng/dropdown';
import { FormsModule } from '@angular/forms';
@Component({
  selector: 'app-admin-home',
  imports: [MenuModule, BadgeModule, RippleModule, AvatarModule, CommonModule, DropdownModule, FormsModule,
    RouterOutlet, SidebarModule, ButtonModule],
  templateUrl: './admin-home.component.html',
  styleUrl: './admin-home.component.scss'
})
export class AdminHomeComponent {

  visible: boolean = false;
  menuItems: MenuItem[];
  userMenuItems: MenuItem[] = [
    { label: 'Profilo', icon: 'pi pi-id-card', routerLink: '/admin/profile' },
    { label: 'Logout', icon: 'pi pi-sign-out', command: () => this.logout() }
  ];
  userName: string = '';
  structures: { id: number, name: string }[] = [];
  selectedStructureId: number | null = null;

  constructor(public router: Router, public authService: AuthService) {
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
    const user = this.authService.getUser();
    console.log("User:", user);
    this.userName = user?.username || '';
    this.structures = user?.structures || [];
    if (this.structures.length > 0) {
      this.selectedStructureId = this.structures[0].id;
    }
    if (this.authService.isSuperAdmin()) {
      this.menuItems.push({
        label: 'Superadmin Panel',
        icon: 'pi pi-shield',
        routerLink: '/admin/superadmin'
      });
    }
  }

  onStructureChange(event: any) {
    this.selectedStructureId = event.value;
    // Qui puoi aggiungere la logica per aggiornare la dashboard o altre parti dell'app
    // Esempio: this.dashboardService.loadDataForStructure(this.selectedStructureId);
  }

  isLoginPage(): boolean {
    return this.router.url === '/admin/login';
  }

  toggleUserMenu(event: Event) {
    const userMenu = document.querySelector('#userMenu');
    if (userMenu) {
      (userMenu as any).toggle(event);
    }
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/admin/login']);
  }

}