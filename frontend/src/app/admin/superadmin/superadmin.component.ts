import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, RouterLinkActive, Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { Subscription } from 'rxjs';

@Component({
    selector: 'app-superadmin',
    standalone: true,
    imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
    templateUrl: './superadmin.component.html',
    styleUrls: ['./superadmin.component.scss']
})
export class SuperadminComponent implements OnInit, OnDestroy {
    isAuthenticated: boolean = false;
    isInitialized: boolean = false;
    private userSubscription!: Subscription;

    constructor(
        private router: Router,
        private authService: AuthService
    ) { }

    ngOnInit(): void {
        console.log('SuperadminComponent: ngOnInit called, isInitialized =', this.isInitialized);
        
        // Prevent duplicate initialization
        if (this.isInitialized) {
            console.log('SuperadminComponent: Already initialized, skipping...');
            return;
        }

        // Wait for localStorage to be available
        if (typeof window === 'undefined' || !window.localStorage) {
            console.log('SuperadminComponent: localStorage not available, waiting...');
            setTimeout(() => this.initializeAuth(), 100);
            return;
        }

        this.initializeAuth();
    }

    private initializeAuth(): void {
        // Prevent duplicate initialization
        if (this.isInitialized) {
            console.log('SuperadminComponent: Auth already initialized, skipping...');
            return;
        }

        // Set initial authentication state
        this.isAuthenticated = this.authService.isLoggedIn();

        this.userSubscription = this.authService.user$.subscribe(user => {
            this.isAuthenticated = !!user;
            console.log('SuperadminComponent: Auth state updated, user =', !!user, 'isInitialized =', this.isInitialized);
            
            // Mark as initialized after auth state is determined
            this.isInitialized = true;

            // Check if user is superadmin
            if (user && !this.authService.isSuperAdmin()) {
                console.log('SuperadminComponent: User is not superadmin, redirecting...');
                this.router.navigate(['/admin/dashboard']);
            }
        });
    }

    ngOnDestroy(): void {
        if (this.userSubscription) {
            this.userSubscription.unsubscribe();
        }
    }
}
