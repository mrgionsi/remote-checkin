import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of, BehaviorSubject } from 'rxjs';
import { AdminHomeComponent } from './admin-home.component';
import { AuthService } from '../../services/auth.service';
import { Menu } from 'primeng/menu';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

describe('AdminHomeComponent', () => {
  let component: AdminHomeComponent;
  let fixture: ComponentFixture<AdminHomeComponent>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockAuthService: jasmine.SpyObj<AuthService>;
  let userSubject: BehaviorSubject<any>;

  const mockUser = {
    username: 'testuser',
    structures: [
      { id: 1, name: 'Structure 1' },
      { id: 2, name: 'Structure 2' }
    ]
  };

  const mockSuperAdminUser = {
    username: 'superadmin',
    structures: [
      { id: 1, name: 'Structure 1' }
    ]
  };

  beforeEach(async () => {
    // Setup mocks
    mockRouter = jasmine.createSpyObj('Router', ['navigate'], {
      url: '/admin/dashboard'
    });
    
    userSubject = new BehaviorSubject(null);
    mockAuthService = jasmine.createSpyObj('AuthService', ['logout', 'isSuperAdmin'], {
      user$: userSubject.asObservable()
    });

    await TestBed.configureTestingModule({
      imports: [
        AdminHomeComponent,
        NoopAnimationsModule
      ],
      providers: [
        { provide: Router, useValue: mockRouter },
        { provide: AuthService, useValue: mockAuthService }
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(AdminHomeComponent);
    component = fixture.componentInstance;
  });

  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    // Reset router URL
    Object.defineProperty(mockRouter, 'url', { value: '/admin/dashboard', writable: true });
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('Component Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should initialize with default values', () => {
      expect(component.visible).toBe(false);
      expect(component.userName).toBe('');
      expect(component.structures).toEqual([]);
      expect(component.selectedStructureId).toBeNull();
    });

    it('should initialize menu items in constructor', () => {
      expect(component.menuItems).toBeDefined();
      expect(component.menuItems.length).toBe(4);
      expect(component.menuItems[0].label).toBe('Dashboard');
      expect(component.menuItems[0].routerLink).toBe('/admin/dashboard');
      expect(component.menuItems[1].label).toBe('Add new Reservation');
      expect(component.menuItems[2].label).toBe('Rooms');
      expect(component.menuItems[3].label).toBe('Settings');
    });

    it('should initialize user menu items', () => {
      expect(component.userMenuItems).toBeDefined();
      expect(component.userMenuItems.length).toBe(3);
      expect(component.userMenuItems[0].label).toBe('Info utente');
      expect(component.userMenuItems[1].label).toBe('Cambia password');
      expect(component.userMenuItems[2].label).toBe('Logout');
    });

    it('should log initialization message', () => {
      spyOn(console, 'log');
      new AdminHomeComponent(mockRouter, mockAuthService);
      expect(console.log).toHaveBeenCalledWith('AdminHomeComponent initialized');
    });
  });

  describe('ngOnInit', () => {
    it('should subscribe to user$ and set user data when user exists', () => {
      mockAuthService.isSuperAdmin.and.returnValue(false);
      
      component.ngOnInit();
      userSubject.next(mockUser);

      expect(component.userName).toBe('testuser');
      expect(component.structures).toEqual(mockUser.structures);
      expect(component.selectedStructureId).toBe(1); // First structure
    });

    it('should save selected structure to localStorage when no saved structure exists', () => {
      mockAuthService.isSuperAdmin.and.returnValue(false);
      
      component.ngOnInit();
      userSubject.next(mockUser);

      expect(localStorage.getItem('selected_structure_id')).toBe('1');
    });

    it('should use saved structure from localStorage when valid', () => {
      localStorage.setItem('selected_structure_id', '2');
      mockAuthService.isSuperAdmin.and.returnValue(false);
      
      component.ngOnInit();
      userSubject.next(mockUser);

      expect(component.selectedStructureId).toBe(2);
    });

    it('should ignore invalid saved structure and use first structure', () => {
      localStorage.setItem('selected_structure_id', '999'); // Invalid ID
      mockAuthService.isSuperAdmin.and.returnValue(false);
      
      component.ngOnInit();
      userSubject.next(mockUser);

      expect(component.selectedStructureId).toBe(1);
      expect(localStorage.getItem('selected_structure_id')).toBe('1');
    });

    it('should add superadmin menu item when user is superadmin', () => {
      mockAuthService.isSuperAdmin.and.returnValue(true);
      const initialMenuLength = component.menuItems.length;
      
      component.ngOnInit();
      userSubject.next(mockSuperAdminUser);

      expect(component.menuItems.length).toBe(initialMenuLength + 1);
      const superadminItem = component.menuItems.find(item => item.label === 'Superadmin Panel');
      expect(superadminItem).toBeDefined();
      expect(superadminItem!.routerLink).toBe('/admin/superadmin');
      expect(superadminItem!.icon).toBe('pi pi-shield');
    });

    it('should not add superadmin menu item when user is not superadmin', () => {
      mockAuthService.isSuperAdmin.and.returnValue(false);
      const initialMenuLength = component.menuItems.length;
      
      component.ngOnInit();
      userSubject.next(mockUser);

      expect(component.menuItems.length).toBe(initialMenuLength);
      const superadminItem = component.menuItems.find(item => item.label === 'Superadmin Panel');
      expect(superadminItem).toBeUndefined();
    });

    it('should navigate to login when user is null', () => {
      component.ngOnInit();
      userSubject.next(null);

      expect(mockRouter.navigate).toHaveBeenCalledWith(['/admin/login']);
    });

    it('should handle user with empty username', () => {
      const userWithoutUsername = { ...mockUser, username: undefined };
      mockAuthService.isSuperAdmin.and.returnValue(false);
      
      component.ngOnInit();
      userSubject.next(userWithoutUsername);

      expect(component.userName).toBe('');
    });

    it('should handle user with no structures', () => {
      const userWithoutStructures = { ...mockUser, structures: [] };
      mockAuthService.isSuperAdmin.and.returnValue(false);
      
      component.ngOnInit();
      userSubject.next(userWithoutStructures);

      expect(component.structures).toEqual([]);
      expect(component.selectedStructureId).toBeNull();
    });

    it('should handle user with undefined structures', () => {
      const userWithUndefinedStructures = { ...mockUser, structures: undefined };
      mockAuthService.isSuperAdmin.and.returnValue(false);
      
      component.ngOnInit();
      userSubject.next(userWithUndefinedStructures);

      expect(component.structures).toEqual([]);
    });

    it('should handle multiple user emissions and duplicate superadmin items', () => {
      mockAuthService.isSuperAdmin.and.returnValue(true);
      
      component.ngOnInit();
      userSubject.next(mockSuperAdminUser);
      
      // Trigger again - this tests the current behavior where duplicates are added
      userSubject.next(mockSuperAdminUser);
      
      const superadminItems = component.menuItems.filter(item => item.label === 'Superadmin Panel');
      expect(superadminItems.length).toBe(2); // Current behavior allows duplicates
    });
  });

  describe('toggleSidebar', () => {
    it('should toggle sidebar visibility from false to true', () => {
      component.visible = false;
      component.toggleSidebar();
      expect(component.visible).toBe(true);
    });

    it('should toggle sidebar visibility from true to false', () => {
      component.visible = true;
      component.toggleSidebar();
      expect(component.visible).toBe(false);
    });

    it('should handle multiple rapid toggles', () => {
      expect(component.visible).toBe(false);
      component.toggleSidebar();
      expect(component.visible).toBe(true);
      component.toggleSidebar();
      expect(component.visible).toBe(false);
      component.toggleSidebar();
      expect(component.visible).toBe(true);
    });
  });

  describe('onStructureChange', () => {
    beforeEach(() => {
      Object.defineProperty(mockRouter, 'url', { value: '/admin/dashboard', writable: true });
    });

    it('should update selected structure ID', () => {
      const event = { value: 2 };
      component.onStructureChange(event);
      expect(component.selectedStructureId).toBe(2);
    });

    it('should save selected structure to localStorage', () => {
      const event = { value: 3 };
      component.onStructureChange(event);
      expect(localStorage.getItem('selected_structure_id')).toBe('3');
    });

    it('should navigate to current URL to reload data', () => {
      const event = { value: 2 };
      component.onStructureChange(event);
      expect(mockRouter.navigate).toHaveBeenCalledWith(['/admin/dashboard']);
    });

    it('should handle null value', () => {
      const event = { value: null };
      component.onStructureChange(event);
      expect(component.selectedStructureId).toBeNull();
      expect(localStorage.getItem('selected_structure_id')).toBe('null');
    });

    it('should handle undefined value', () => {
      const event = { value: undefined };
      component.onStructureChange(event);
      expect(component.selectedStructureId).toBeUndefined();
      expect(localStorage.getItem('selected_structure_id')).toBe('undefined');
    });

    it('should handle different router URLs', () => {
      Object.defineProperty(mockRouter, 'url', { value: '/admin/rooms' });
      const event = { value: 1 };
      component.onStructureChange(event);
      expect(mockRouter.navigate).toHaveBeenCalledWith(['/admin/rooms']);
    });
  });

  describe('isLoginPage', () => {
    it('should return true when on login page', () => {
      Object.defineProperty(mockRouter, 'url', { value: '/admin/login', writable: true });
      expect(component.isLoginPage()).toBe(true);
    });

    it('should return false when not on login page', () => {
      Object.defineProperty(mockRouter, 'url', { value: '/admin/dashboard', writable: true });
      expect(component.isLoginPage()).toBe(false);
    });

    it('should return false for similar but different paths', () => {
      Object.defineProperty(mockRouter, 'url', { value: '/admin/login-help', writable: true });
      expect(component.isLoginPage()).toBe(false);
    });

    it('should handle empty URL', () => {
      Object.defineProperty(mockRouter, 'url', { value: '', writable: true });
      expect(component.isLoginPage()).toBe(false);
    });

    it('should handle login page with query parameters', () => {
      Object.defineProperty(mockRouter, 'url', { value: '/admin/login?redirect=dashboard', writable: true });
      expect(component.isLoginPage()).toBe(false);
    });
  });

  describe('toggleUserMenu', () => {
    it('should call toggle on userMenu with event', () => {
      const mockEvent = new Event('click');
      component.userMenu = jasmine.createSpyObj('Menu', ['toggle']);
      
      component.toggleUserMenu(mockEvent);
      
      expect(component.userMenu.toggle).toHaveBeenCalledWith(mockEvent);
    });

    it('should throw error when userMenu is undefined', () => {
      const mockEvent = new Event('click');
      component.userMenu = undefined as any;
      
      expect(() => {
        component.toggleUserMenu(mockEvent);
      }).toThrow();
    });
  });

  describe('showUserInfo', () => {
    it('should navigate to admin info page', () => {
      component.showUserInfo();
      expect(mockRouter.navigate).toHaveBeenCalledWith(['/admin/admin-info']);
    });
  });

  describe('logout', () => {
    it('should call authService logout and navigate to login', () => {
      component.logout();
      
      expect(mockAuthService.logout).toHaveBeenCalled();
      expect(mockRouter.navigate).toHaveBeenCalledWith(['/admin/login']);
    });
  });

  describe('User Menu Items Commands', () => {
    it('should execute showUserInfo when Info utente is clicked', () => {
      spyOn(component, 'showUserInfo');
      const infoUserItem = component.userMenuItems.find(item => item.label === 'Info utente');
      
      expect(infoUserItem).toBeDefined();
      expect(infoUserItem!.command).toBeDefined();
      infoUserItem!.command!();
      
      expect(component.showUserInfo).toHaveBeenCalled();
    });

    it('should execute logout when Logout is clicked', () => {
      spyOn(component, 'logout');
      const logoutItem = component.userMenuItems.find(item => item.label === 'Logout');
      
      expect(logoutItem).toBeDefined();
      expect(logoutItem!.command).toBeDefined();
      logoutItem!.command!();
      
      expect(component.logout).toHaveBeenCalled();
    });

    it('should have correct router link for change password', () => {
      const changePasswordItem = component.userMenuItems.find(item => item.label === 'Cambia password');
      
      expect(changePasswordItem).toBeDefined();
      expect(changePasswordItem!.routerLink).toBe('/admin/change-password');
    });

    it('should have correct icons for all user menu items', () => {
      expect(component.userMenuItems[0].icon).toBe('pi pi-user');
      expect(component.userMenuItems[1].icon).toBe('pi pi-key');
      expect(component.userMenuItems[2].icon).toBe('pi pi-sign-out');
    });
  });

  describe('Edge Cases and Error Handling', () => {
    it('should handle multiple rapid user$ emissions', () => {
      mockAuthService.isSuperAdmin.and.returnValue(false);
      
      component.ngOnInit();
      
      // Emit multiple users rapidly
      userSubject.next(mockUser);
      userSubject.next({ ...mockUser, username: 'user2' });
      userSubject.next({ ...mockUser, username: 'user3' });
      
      expect(component.userName).toBe('user3');
    });

    it('should handle localStorage getItem errors', () => {
      spyOn(localStorage, 'getItem').and.throwError('Storage error');
      mockAuthService.isSuperAdmin.and.returnValue(false);
      
      expect(() => {
        component.ngOnInit();
        userSubject.next(mockUser);
      }).not.toThrow();
    });

    it('should handle localStorage setItem errors', () => {
      spyOn(localStorage, 'setItem').and.throwError('Storage error');
      mockAuthService.isSuperAdmin.and.returnValue(false);
      
      expect(() => {
        component.onStructureChange({ value: 1 });
      }).not.toThrow();
    });

    it('should handle malformed user data gracefully', () => {
      const malformedUser = {
        username: null,
        structures: 'not-an-array'
      };
      mockAuthService.isSuperAdmin.and.returnValue(false);
      
      component.ngOnInit();
      userSubject.next(malformedUser);
      
      expect(component.userName).toBe('');
      expect(component.structures).toEqual([]);
    });
  });

  describe('Component State Management', () => {
    it('should maintain consistent state after multiple operations', () => {
      mockAuthService.isSuperAdmin.and.returnValue(false);
      
      // Initialize component
      component.ngOnInit();
      userSubject.next(mockUser);
      
      // Toggle sidebar
      component.toggleSidebar();
      expect(component.visible).toBe(true);
      
      // Change structure
      component.onStructureChange({ value: 2 });
      expect(component.selectedStructureId).toBe(2);
      
      // Verify user data is still intact
      expect(component.userName).toBe('testuser');
      expect(component.structures).toEqual(mockUser.structures);
    });

    it('should handle component reinitialization', () => {
      // Create new component instance
      const newComponent = new AdminHomeComponent(mockRouter, mockAuthService);
      expect(newComponent.visible).toBe(false);
      expect(newComponent.selectedStructureId).toBeNull();
      expect(newComponent.userName).toBe('');
    });
  });

  describe('Integration with PrimeNG Components', () => {
    it('should have correct menu item structure for PrimeNG Menu', () => {
      component.menuItems.forEach(item => {
        expect(item.label).toBeDefined();
        expect(item.icon).toBeDefined();
        expect(item.routerLink).toBeDefined();
      });
    });

    it('should have correct user menu item structure for PrimeNG Menu', () => {
      component.userMenuItems.forEach(item => {
        expect(item.label).toBeDefined();
        expect(item.icon).toBeDefined();
        expect(item.command || item.routerLink).toBeDefined();
      });
    });

    it('should have valid PrimeNG icon classes', () => {
      const allItems = [...component.menuItems, ...component.userMenuItems];
      allItems.forEach(item => {
        expect(item.icon).toMatch(/^pi pi-/);
      });
    });
  });

  describe('Menu Item Validation', () => {
    it('should have unique menu item labels', () => {
      const labels = component.menuItems.map(item => item.label);
      const uniqueLabels = [...new Set(labels)];
      expect(labels.length).toBe(uniqueLabels.length);
    });

    it('should have valid router links for main menu items', () => {
      component.menuItems.forEach(item => {
        expect(item.routerLink).toMatch(/^\/admin\//);
      });
    });

    it('should have consistent icon naming pattern', () => {
      const allItems = [...component.menuItems, ...component.userMenuItems];
      allItems.forEach(item => {
        expect(item.icon).toMatch(/^pi pi-[a-z-]+$/);
      });
    });
  });

  describe('localStorage Integration', () => {
    it('should handle localStorage quota exceeded error', () => {
      spyOn(localStorage, 'setItem').and.throwError({ name: 'QuotaExceededError' });
      
      expect(() => {
        component.onStructureChange({ value: 1 });
      }).not.toThrow();
    });

    it('should handle corrupted localStorage data', () => {
      localStorage.setItem('selected_structure_id', 'corrupted-data');
      mockAuthService.isSuperAdmin.and.returnValue(false);
      
      component.ngOnInit();
      userSubject.next(mockUser);
      
      // Should fall back to first structure
      expect(component.selectedStructureId).toBe(1);
    });

    it('should handle numeric string parsing correctly', () => {
      localStorage.setItem('selected_structure_id', '2');
      mockAuthService.isSuperAdmin.and.returnValue(false);
      
      component.ngOnInit();
      userSubject.next(mockUser);
      
      expect(component.selectedStructureId).toBe(2);
      expect(typeof component.selectedStructureId).toBe('number');
    });
  });

  describe('Lifecycle and Subscription Management', () => {
    it('should handle subscription to user$ observable', () => {
      mockAuthService.isSuperAdmin.and.returnValue(false);
      spyOn(userSubject, 'subscribe').and.callThrough();
      
      component.ngOnInit();
      
      expect(mockAuthService.user$.subscribe).toHaveBeenCalled();
    });

    it('should handle falsy user data properly', () => {
      component.ngOnInit();
      
      // Test various falsy values
      userSubject.next(false);
      expect(mockRouter.navigate).toHaveBeenCalledWith(['/admin/login']);
      
      userSubject.next(0);
      expect(mockRouter.navigate).toHaveBeenCalledWith(['/admin/login']);
      
      userSubject.next('');
      expect(mockRouter.navigate).toHaveBeenCalledWith(['/admin/login']);
    });
  });
});
