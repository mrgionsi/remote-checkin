import { Component, ViewChild, OnInit, OnDestroy } from '@angular/core';
import { MenuItem } from 'primeng/api';
import { MenuModule } from 'primeng/menu';
import { BadgeModule } from 'primeng/badge';
import { RippleModule } from 'primeng/ripple';
import { AvatarModule } from 'primeng/avatar';
import { CommonModule } from '@angular/common';
import { Router, RouterOutlet } from '@angular/router';
import { SidebarModule } from 'primeng/sidebar';
import { ButtonModule } from 'primeng/button';
import { AuthService } from '../../services/auth.service';
import { DropdownModule } from 'primeng/dropdown';
import { FormsModule } from '@angular/forms';
import { Menu } from 'primeng/menu';
import { Subscription } from 'rxjs';
import { TranslocoPipe, TranslocoService } from '@jsverse/transloco';

@Component({
  selector: 'app-admin-home',
  imports: [MenuModule, BadgeModule, RippleModule, AvatarModule, CommonModule, DropdownModule, FormsModule,
    RouterOutlet, SidebarModule, ButtonModule, TranslocoPipe],
  templateUrl: './admin-home.component.html',
  styleUrl: './admin-home.component.scss'
})
export class AdminHomeComponent implements OnInit, OnDestroy {

  visible: boolean = false;
  menuItems: MenuItem[] = [];
  userMenuItems: MenuItem[] = [];
  userName: string = '';
  structures: { id: number, name: string }[] = [];
  selectedStructureId: number | null = null;

  @ViewChild('userMenu') userMenu!: Menu;
  private userSubscription!: Subscription;

  constructor(
    public router: Router,
    public authService: AuthService,
    private readonly translocoService: TranslocoService
  ) {
    if (typeof window !== 'undefined' && window.localStorage) {
      const lang = localStorage.getItem('appLang') || 'en';
      this.translocoService.setActiveLang(lang);

    }


  }

  toggleSidebar() {
    this.visible = !this.visible;
  }

  ngOnInit() {

    this.translocoService.selectTranslateObject([
      'dashboard-label',
      'add-reservation-label',
      'rooms-label',
      'settings-label',
      'user-info-label',
      'change-password-label'
    ]).subscribe((translations: any) => {
      this.menuItems = [
        { label: translations[0], icon: 'pi pi-chart-line', routerLink: '/admin/dashboard' },
        { label: translations[1], icon: 'pi pi-plus', routerLink: '/admin/create-reservation' },
        { label: translations[2], icon: 'pi pi-warehouse', routerLink: '/admin/rooms' },
        { label: translations[3], icon: 'pi pi-cog', routerLink: '/admin/settings' }
      ];
      if (this.authService.isSuperAdmin()) {
        this.menuItems.push({
          label: 'Superadmin Panel',
          icon: 'pi pi-shield',
          routerLink: '/admin/superadmin'
        });
      }
      this.userMenuItems = [
        {
          label: translations[4],
          icon: 'pi pi-user',
          command: () => this.showUserInfo()
        },
        {
          label: translations[5],
          icon: 'pi pi-key',
          routerLink: '/admin/change-password'
        },
        {
          label: 'Logout',
          icon: 'pi pi-sign-out',
          command: () => this.logout()
        }
      ];
    });
    this.userSubscription = this.authService.user$.subscribe(user => {
      if (user) {
        this.userName = user?.username || '';
        this.structures = user?.structures || [];

        const savedStructureId = localStorage.getItem('selected_structure_id');
        if (savedStructureId && this.structures.some(s => s.id === +savedStructureId)) {
          this.selectedStructureId = +savedStructureId;
        } else if (this.structures.length > 0) {
          this.selectedStructureId = this.structures[0].id;
          localStorage.setItem('selected_structure_id', String(this.selectedStructureId));
        }
        console.log(this.authService.isSuperAdmin())

      }
      else {
        this.router.navigate(['/admin/login']);
      }
    });

  }

  ngOnDestroy() {
    if (this.userSubscription) {
      this.userSubscription.unsubscribe();
    }
  }

  onStructureChange(event: any) {
    this.selectedStructureId = event.value;
    localStorage.setItem('selected_structure_id', String(this.selectedStructureId));
    // Force a full page reload to ensure data is refreshed everywhere
    window.location.reload();
    // Alternatively, use an event emitter/service for a more Angular way
  }

  isLoginPage(): boolean {
    //console.log('Current URL:', this.router.url);
    return this.router.url === '/admin/login';
  }


  toggleUserMenu(event: Event) {
    this.userMenu.toggle(event);
  }

  showUserInfo() {
    this.router.navigate(['/admin/admin-info']);
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/admin/login']);
  }

}