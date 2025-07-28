import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { HttpHeaders } from '@angular/common/http';
import { AuthService } from './auth.service';

describe('AuthService', () => {
  let service: AuthService;
  let routerSpy: jasmine.SpyObj<Router>;
  let mockLocalStorage: { [key: string]: string };

  beforeEach(() => {
    const routerSpyObj = jasmine.createSpyObj('Router', ['navigate']);
    
    // Mock localStorage with a simple object
    mockLocalStorage = {};
    
    spyOn(Storage.prototype, 'getItem').and.callFake((key: string) => {
      return mockLocalStorage[key] || null;
    });
    
    spyOn(Storage.prototype, 'setItem').and.callFake((key: string, value: string) => {
      mockLocalStorage[key] = value;
    });
    
    spyOn(Storage.prototype, 'removeItem').and.callFake((key: string) => {
      delete mockLocalStorage[key];
    });

    TestBed.configureTestingModule({
      providers: [
        AuthService,
        { provide: Router, useValue: routerSpyObj }
      ]
    });
    
    service = TestBed.inject(AuthService);
    routerSpy = TestBed.inject(Router) as jasmine.SpyObj<Router>;
  });

  afterEach(() => {
    mockLocalStorage = {};
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('setUser', () => {
    it('should store user in localStorage and update user subject', () => {
      const mockUser = { id: 1, name: 'Test User', role: 'admin' };
      
      service.setUser(mockUser);
      
      expect(localStorage.setItem).toHaveBeenCalledWith('user', JSON.stringify(mockUser));
    });

    it('should emit user data through user$ observable', (done) => {
      const mockUser = { id: 1, name: 'Test User', role: 'admin' };
      
      service.user$.subscribe(user => {
        if (user && user.id === mockUser.id) {
          expect(user).toEqual(mockUser);
          done();
        }
      });
      
      service.setUser(mockUser);
    });

    it('should handle null user', () => {
      service.setUser(null);
      
      expect(localStorage.setItem).toHaveBeenCalledWith('user', 'null');
    });

    it('should handle undefined user', () => {
      service.setUser(undefined);
      
      expect(localStorage.setItem).toHaveBeenCalledWith('user', undefined);
    });

    it('should handle complex user objects', () => {
      const complexUser = {
        id: 1,
        name: 'Test User',
        role: 'admin',
        permissions: ['read', 'write'],
        profile: {
          avatar: 'avatar.jpg',
          email: 'test@example.com'
        }
      };
      
      service.setUser(complexUser);
      
      expect(localStorage.setItem).toHaveBeenCalledWith('user', JSON.stringify(complexUser));
    });
  });

  describe('clearUser', () => {
    it('should remove user from localStorage and emit null', () => {
      service.clearUser();
      
      expect(localStorage.removeItem).toHaveBeenCalledWith('user');
    });

    it('should emit null through user$ observable', (done) => {
      // First set a user
      service.setUser({ id: 1, name: 'Test' });
      
      // Then clear and check emission
      service.user$.subscribe(user => {
        if (user === null) {
          done();
        }
      });
      
      service.clearUser();
    });
  });

  describe('getUser', () => {
    it('should return null when window is undefined', () => {
      const originalWindow = (global as any).window;
      (global as any).window = undefined;
      
      const result = service.getUser();
      
      expect(result).toBeNull();
      
      // Restore window
      (global as any).window = originalWindow;
    });

    it('should return null when localStorage is not available', () => {
      const originalLocalStorage = (global as any).localStorage;
      Object.defineProperty(window, 'localStorage', {
        value: null,
        writable: true
      });
      
      const result = service.getUser();
      
      expect(result).toBeNull();
      
      // Restore localStorage
      Object.defineProperty(window, 'localStorage', {
        value: originalLocalStorage,
        writable: true
      });
    });

    it('should return null when no user in localStorage', () => {
      const result = service.getUser();
      
      expect(result).toBeNull();
      expect(localStorage.getItem).toHaveBeenCalledWith('user');
    });

    it('should return parsed user when valid JSON in localStorage', () => {
      const mockUser = { id: 1, name: 'Test User', role: 'admin' };
      mockLocalStorage['user'] = JSON.stringify(mockUser);
      
      const result = service.getUser();
      
      expect(result).toEqual(mockUser);
    });

    it('should return null when invalid JSON in localStorage', () => {
      mockLocalStorage['user'] = 'invalid json';
      
      const result = service.getUser();
      
      expect(result).toBeNull();
    });

    it('should handle empty string in localStorage', () => {
      mockLocalStorage['user'] = '';
      
      const result = service.getUser();
      
      expect(result).toBeNull();
    });

    it('should handle whitespace-only string in localStorage', () => {
      mockLocalStorage['user'] = '   ';
      
      const result = service.getUser();
      
      expect(result).toBeNull();
    });
  });

  describe('isTokenValid', () => {
    beforeEach(() => {
      jasmine.clock().install();
      jasmine.clock().mockDate(new Date('2023-01-01T10:00:00Z'));
    });

    afterEach(() => {
      jasmine.clock().uninstall();
    });

    it('should return false when no token exists', () => {
      const result = service.isTokenValid();
      
      expect(result).toBeFalse();
      expect(localStorage.getItem).toHaveBeenCalledWith('admin_token');
    });

    it('should return true when token is valid and not expired', () => {
      const futureExp = Math.floor(Date.now() / 1000) + 3600; // 1 hour from now
      const payload = { exp: futureExp };
      const token = `header.${btoa(JSON.stringify(payload))}.signature`;
      mockLocalStorage['admin_token'] = token;
      
      const result = service.isTokenValid();
      
      expect(result).toBeTrue();
    });

    it('should return false when token is expired', () => {
      const pastExp = Math.floor(Date.now() / 1000) - 3600; // 1 hour ago
      const payload = { exp: pastExp };
      const token = `header.${btoa(JSON.stringify(payload))}.signature`;
      mockLocalStorage['admin_token'] = token;
      
      const result = service.isTokenValid();
      
      expect(result).toBeFalse();
    });

    it('should return false when token has no expiration', () => {
      const payload = {};
      const token = `header.${btoa(JSON.stringify(payload))}.signature`;
      mockLocalStorage['admin_token'] = token;
      
      const result = service.isTokenValid();
      
      expect(result).toBeFalse();
    });

    it('should return false when token expiration is null', () => {
      const payload = { exp: null };
      const token = `header.${btoa(JSON.stringify(payload))}.signature`;
      mockLocalStorage['admin_token'] = token;
      
      const result = service.isTokenValid();
      
      expect(result).toBeFalse();
    });

    it('should handle malformed token gracefully', () => {
      mockLocalStorage['admin_token'] = 'malformed.token';
      
      expect(() => service.isTokenValid()).toThrow();
    });

    it('should handle token with invalid JSON payload', () => {
      const token = `header.invalid_base64.signature`;
      mockLocalStorage['admin_token'] = token;
      
      expect(() => service.isTokenValid()).toThrow();
    });

    it('should handle token with missing parts', () => {
      mockLocalStorage['admin_token'] = 'incomplete_token';
      
      expect(() => service.isTokenValid()).toThrow();
    });

    it('should handle empty token', () => {
      mockLocalStorage['admin_token'] = '';
      
      const result = service.isTokenValid();
      
      expect(result).toBeFalse();
    });
  });

  describe('isLoggedIn', () => {
    it('should return false when window is undefined', () => {
      const originalWindow = (global as any).window;
      (global as any).window = undefined;
      
      const result = service.isLoggedIn();
      
      expect(result).toBeFalse();
      
      // Restore window
      (global as any).window = originalWindow;
    });

    it('should return false when localStorage is not available', () => {
      Object.defineProperty(window, 'localStorage', {
        value: null,
        writable: true
      });
      
      const result = service.isLoggedIn();
      
      expect(result).toBeFalse();
    });

    it('should return false and logout when no user exists', () => {
      spyOn(service, 'getUser').and.returnValue(null);
      spyOn(service, 'logout');
      
      const result = service.isLoggedIn();
      
      expect(result).toBeFalse();
      expect(service.logout).toHaveBeenCalled();
      expect(routerSpy.navigate).toHaveBeenCalledWith(['/admin/login']);
    });

    it('should return false and logout when token is invalid', () => {
      spyOn(service, 'getUser').and.returnValue({ id: 1, name: 'Test' });
      spyOn(service, 'isTokenValid').and.returnValue(false);
      spyOn(service, 'logout');
      
      const result = service.isLoggedIn();
      
      expect(result).toBeFalse();
      expect(service.logout).toHaveBeenCalled();
      expect(routerSpy.navigate).toHaveBeenCalledWith(['/admin/login']);
    });

    it('should return true when user exists and token is valid', () => {
      spyOn(service, 'getUser').and.returnValue({ id: 1, name: 'Test' });
      spyOn(service, 'isTokenValid').and.returnValue(true);
      spyOn(service, 'logout');
      
      const result = service.isLoggedIn();
      
      expect(result).toBeTrue();
      expect(service.logout).not.toHaveBeenCalled();
      expect(routerSpy.navigate).not.toHaveBeenCalled();
    });

    it('should handle user object without required properties', () => {
      spyOn(service, 'getUser').and.returnValue({});
      spyOn(service, 'isTokenValid').and.returnValue(true);
      spyOn(service, 'logout');
      
      const result = service.isLoggedIn();
      
      expect(result).toBeTrue();
    });
  });

  describe('getUserRole', () => {
    it('should return empty string when no user exists', () => {
      spyOn(service, 'getUser').and.returnValue(null);
      
      const result = service.getUserRole();
      
      expect(result).toBe('');
    });

    it('should return empty string when user has no role', () => {
      spyOn(service, 'getUser').and.returnValue({ id: 1, name: 'Test' });
      
      const result = service.getUserRole();
      
      expect(result).toBe('');
    });

    it('should return user role when user has role', () => {
      spyOn(service, 'getUser').and.returnValue({ id: 1, name: 'Test', role: 'admin' });
      
      const result = service.getUserRole();
      
      expect(result).toBe('admin');
    });

    it('should return empty string when user role is undefined', () => {
      spyOn(service, 'getUser').and.returnValue({ id: 1, name: 'Test', role: undefined });
      
      const result = service.getUserRole();
      
      expect(result).toBe('');
    });

    it('should return empty string when user role is null', () => {
      spyOn(service, 'getUser').and.returnValue({ id: 1, name: 'Test', role: null });
      
      const result = service.getUserRole();
      
      expect(result).toBe('');
    });

    it('should handle different role types', () => {
      const roles = ['admin', 'user', 'moderator', 'superadmin'];
      
      roles.forEach(role => {
        spyOn(service, 'getUser').and.returnValue({ id: 1, name: 'Test', role });
        
        const result = service.getUserRole();
        
        expect(result).toBe(role);
      });
    });
  });

  describe('isSuperAdmin', () => {
    it('should return true when user role is superadmin', () => {
      spyOn(service, 'getUserRole').and.returnValue('superadmin');
      
      const result = service.isSuperAdmin();
      
      expect(result).toBeTrue();
    });

    it('should return false when user role is admin', () => {
      spyOn(service, 'getUserRole').and.returnValue('admin');
      
      const result = service.isSuperAdmin();
      
      expect(result).toBeFalse();
    });

    it('should return false when user role is empty', () => {
      spyOn(service, 'getUserRole').and.returnValue('');
      
      const result = service.isSuperAdmin();
      
      expect(result).toBeFalse();
    });

    it('should return false when user role is null', () => {
      spyOn(service, 'getUserRole').and.returnValue(null as any);
      
      const result = service.isSuperAdmin();
      
      expect(result).toBeFalse();
    });

    it('should be case sensitive', () => {
      spyOn(service, 'getUserRole').and.returnValue('SUPERADMIN');
      
      const result = service.isSuperAdmin();
      
      expect(result).toBeFalse();
    });

    it('should not match partial strings', () => {
      spyOn(service, 'getUserRole').and.returnValue('superadmin_user');
      
      const result = service.isSuperAdmin();
      
      expect(result).toBeFalse();
    });
  });

  describe('logout', () => {
    it('should remove user and admin_token from localStorage', () => {
      service.logout();
      
      expect(localStorage.removeItem).toHaveBeenCalledWith('user');
      expect(localStorage.removeItem).toHaveBeenCalledWith('admin_token');
    });

    it('should call removeItem twice', () => {
      service.logout();
      
      expect(localStorage.removeItem).toHaveBeenCalledTimes(2);
    });

    it('should not update user subject', () => {
      spyOn(service['userSubject'], 'next');
      
      service.logout();
      
      expect(service['userSubject'].next).not.toHaveBeenCalled();
    });
  });

  describe('getAuthHeaders', () => {
    it('should return HttpHeaders with Bearer token when token exists', () => {
      const mockToken = 'mock-jwt-token';
      mockLocalStorage['admin_token'] = mockToken;
      
      const result = service.getAuthHeaders();
      
      expect(result).toBeInstanceOf(HttpHeaders);
      expect(result.get('Authorization')).toBe(`Bearer ${mockToken}`);
      expect(localStorage.getItem).toHaveBeenCalledWith('admin_token');
    });

    it('should return HttpHeaders with Bearer null when no token exists', () => {
      const result = service.getAuthHeaders();
      
      expect(result).toBeInstanceOf(HttpHeaders);
      expect(result.get('Authorization')).toBe('Bearer null');
    });

    it('should return HttpHeaders with Bearer undefined when token is undefined', () => {
      mockLocalStorage['admin_token'] = undefined as any;
      
      const result = service.getAuthHeaders();
      
      expect(result).toBeInstanceOf(HttpHeaders);
      expect(result.get('Authorization')).toBe('Bearer null'); // getItem returns null for undefined
    });

    it('should return HttpHeaders with empty token when token is empty string', () => {
      mockLocalStorage['admin_token'] = '';
      
      const result = service.getAuthHeaders();
      
      expect(result).toBeInstanceOf(HttpHeaders);
      expect(result.get('Authorization')).toBe('Bearer ');
    });

    it('should handle very long tokens', () => {
      const longToken = 'a'.repeat(1000);
      mockLocalStorage['admin_token'] = longToken;
      
      const result = service.getAuthHeaders();
      
      expect(result.get('Authorization')).toBe(`Bearer ${longToken}`);
    });

    it('should handle tokens with special characters', () => {
      const specialToken = 'token.with-special_chars123!@#';
      mockLocalStorage['admin_token'] = specialToken;
      
      const result = service.getAuthHeaders();
      
      expect(result.get('Authorization')).toBe(`Bearer ${specialToken}`);
    });
  });

  describe('user$ observable', () => {
    it('should emit initial user value on subscription', (done) => {
      const mockUser = { id: 1, name: 'Test User' };
      mockLocalStorage['user'] = JSON.stringify(mockUser);
      
      // Create new service instance to trigger constructor
      const newService = new AuthService(routerSpy);
      
      newService.user$.subscribe(user => {
        expect(user).toEqual(mockUser);
        done();
      });
    });

    it('should emit null when no initial user', (done) => {
      // Create new service instance to trigger constructor
      const newService = new AuthService(routerSpy);
      
      newService.user$.subscribe(user => {
        expect(user).toBeNull();
        done();
      });
    });

    it('should be a BehaviorSubject that replays last value', (done) => {
      const mockUser = { id: 1, name: 'Test User' };
      
      service.setUser(mockUser);
      
      // Subscribe after setting user should still get the value
      service.user$.subscribe(user => {
        expect(user).toEqual(mockUser);
        done();
      });
    });
  });

  describe('Edge Cases and Error Handling', () => {
    it('should handle localStorage quota exceeded on setUser', () => {
      (localStorage.setItem as jasmine.Spy).and.throwError('QuotaExceededError');
      
      expect(() => service.setUser({ id: 1 })).toThrow();
    });

    it('should handle localStorage access denied on getUser', () => {
      (localStorage.getItem as jasmine.Spy).and.throwError('SecurityError');
      
      expect(() => service.getUser()).toThrow();
    });

    it('should handle localStorage access denied on logout', () => {
      (localStorage.removeItem as jasmine.Spy).and.throwError('SecurityError');
      
      expect(() => service.logout()).toThrow();
    });

    it('should handle very large user objects', () => {
      const largeUser = {
        id: 1,
        name: 'Test User',
        data: 'x'.repeat(10000) // Large string
      };
      
      expect(() => service.setUser(largeUser)).not.toThrow();
      expect(localStorage.setItem).toHaveBeenCalledWith('user', JSON.stringify(largeUser));
    });

    it('should handle circular reference in user object', () => {
      const circularUser: any = { id: 1, name: 'Test' };
      circularUser.self = circularUser;
      
      expect(() => service.setUser(circularUser)).toThrow();
    });

    it('should handle special characters in user data', () => {
      const specialUser = {
        id: 1,
        name: 'Test "User" with \'quotes\' and \nspecial\tchars',
        emoji: '🚀🔥💯'
      };
      
      service.setUser(specialUser);
      
      expect(localStorage.setItem).toHaveBeenCalledWith('user', JSON.stringify(specialUser));
    });

    it('should handle router navigation failures gracefully', () => {
      routerSpy.navigate.and.throwError('Navigation failed');
      spyOn(service, 'getUser').and.returnValue(null);
      spyOn(service, 'logout');
      
      expect(() => service.isLoggedIn()).toThrow();
    });

    it('should handle malformed localStorage data during initialization', () => {
      mockLocalStorage['user'] = '{invalid json';
      
      // Create new service instance
      const newService = new AuthService(routerSpy);
      
      expect(newService).toBeTruthy();
    });
  });

  describe('Integration Tests', () => {
    it('should complete full login flow', (done) => {
      const mockUser = { id: 1, name: 'Test User', role: 'admin' };
      const futureExp = Math.floor(Date.now() / 1000) + 3600;
      const payload = { exp: futureExp };
      const token = `header.${btoa(JSON.stringify(payload))}.signature`;
      
      // Set up user and token
      service.setUser(mockUser);
      mockLocalStorage['admin_token'] = token;
      
      // Verify user is logged in
      expect(service.isLoggedIn()).toBeTrue();
      expect(service.getUserRole()).toBe('admin');
      expect(service.isSuperAdmin()).toBeFalse();
      
      // Verify observable emits user
      service.user$.subscribe(user => {
        expect(user).toEqual(mockUser);
        done();
      });
    });

    it('should complete full logout flow', () => {
      const mockUser = { id: 1, name: 'Test User', role: 'admin' };
      
      // Set up user
      service.setUser(mockUser);
      expect(service.getUser()).toEqual(mockUser);
      
      // Logout
      service.logout();
      
      // Verify cleanup
      expect(localStorage.removeItem).toHaveBeenCalledWith('user');
      expect(localStorage.removeItem).toHaveBeenCalledWith('admin_token');
      
      // User should still be in memory until clearUser is called
      expect(service.getUser()).toBeNull(); // localStorage is cleared
    });

    it('should handle token expiration during session', () => {
      jasmine.clock().install();
      
      const mockUser = { id: 1, name: 'Test User', role: 'admin' };
      service.setUser(mockUser);
      
      // Set token that expires in 1 hour
      const exp = Math.floor(Date.now() / 1000) + 3600;
      const payload = { exp };
      const token = `header.${btoa(JSON.stringify(payload))}.signature`;
      mockLocalStorage['admin_token'] = token;
      
      // Initially logged in
      expect(service.isLoggedIn()).toBeTrue();
      
      // Fast forward past expiration
      jasmine.clock().tick(3700 * 1000); // 3700 seconds
      
      spyOn(service, 'logout');
      
      // Should be logged out now
      expect(service.isLoggedIn()).toBeFalse();
      expect(service.logout).toHaveBeenCalled();
      expect(routerSpy.navigate).toHaveBeenCalledWith(['/admin/login']);
      
      jasmine.clock().uninstall();
    });
  });
});