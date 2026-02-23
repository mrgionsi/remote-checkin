import { Routes } from '@angular/router';
import { LanguageComponent } from './language/language.component';
import { RemoteCheckinComponent } from './remote-checkin/remote-checkin.component';
import { DashboardComponent } from './admin/dashboard/dashboard.component';
import { CreateReservationComponent } from './admin/create-reservation/create-reservation.component';
import { AdminHomeComponent } from './admin/admin-home/admin-home.component';
import { RoomComponent } from './admin/room/room.component';
import { ReservationCheckComponent } from './reservation-check/reservation-check.component';
import { DetailReservationComponent } from './detail-reservation/detail-reservation.component';
import { LoginComponent } from './admin/login/login.component';
import { authGuard } from './guards/auth.guard';
import { superadminGuard } from './guards/superadmin.guard';
import { AdminInfoComponent } from './admin/admin-info/admin-info.component';
import { SettingsComponent } from './admin/settings/settings.component';
import { SuperadminComponent } from './admin/superadmin/superadmin.component';
import { SuperadminDashboardComponent } from './admin/superadmin/superadmin-dashboard/superadmin-dashboard.component';
import { SuperadminStructuresComponent } from './admin/superadmin/structures/structures.component';
import { SuperadminUsersComponent } from './admin/superadmin/users/users.component';
import { SuperadminAssociationsComponent } from './admin/superadmin/associations/associations.component';
import { CheckinCompleteComponent } from './checkin-complete/checkin-complete.component';
import { ChangePasswordComponent } from './admin/change-password/change-password.component';
import { ActivityTimelineComponent } from './admin/activity-timeline/activity-timeline.component';

export const routes: Routes = [
    {
        path: 'landing',
        loadComponent: () => import('./landing/landing.component').then(m => m.LandingComponent)
    },
    {
        path: 'pricing',
        loadComponent: () => import('./pricing-details/pricing-details.component').then(m => m.PricingDetailsComponent)
    },
    {
        path: 'faq',
        loadComponent: () => import('./faq/faq.component').then(m => m.FAQComponent)
    },
    { path: '', component: LanguageComponent },
    { path: ':id', component: LanguageComponent }, // Optional reservation ID in language selection
    { path: 'reservation-check/:code', component: ReservationCheckComponent }, // Check reservation
    { path: ':id/remote-checkin/:code', component: RemoteCheckinComponent }, // Dynamic check-in with reservation ID
    { path: 'checkin-complete/:id', component: CheckinCompleteComponent },
    { path: 'remote-checkin/:code', redirectTo: 'reservation-check/:code', pathMatch: 'full' }, // Redirect if no ID
    { path: 'admin', redirectTo: 'admin/dashboard', pathMatch: 'full' }, // Add this redirect

    {
        path: 'admin',
        component: AdminHomeComponent, // Acts as the parent,
        children: [
            { path: 'login', component: LoginComponent },
            { path: 'dashboard', component: DashboardComponent, canActivate: [authGuard] },
            { path: 'rooms', component: RoomComponent, canActivate: [authGuard] },
            { path: 'reservation-details/:id_reservation', component: DetailReservationComponent, canActivate: [authGuard] },
            { path: 'create-reservation', component: CreateReservationComponent, canActivate: [authGuard] },
            { path: 'admin-info', component: AdminInfoComponent, canActivate: [authGuard] },
            { path: 'change-password', component: ChangePasswordComponent, canActivate: [authGuard] },
            { path: 'settings', component: SettingsComponent, canActivate: [authGuard] },
            { path: 'activity', component: ActivityTimelineComponent, canActivate: [authGuard] },
            {
                path: 'superadmin',
                component: SuperadminComponent,
                canActivate: [superadminGuard],
                children: [
                    { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
                    { path: 'dashboard', component: SuperadminDashboardComponent },
                    { path: 'activity', component: ActivityTimelineComponent },
                    { path: 'structures', component: SuperadminStructuresComponent },
                    { path: 'users', component: SuperadminUsersComponent },
                    { path: 'associations', component: SuperadminAssociationsComponent },
                ]
            },
            { path: '', redirectTo: 'dashboard', pathMatch: 'full' },

        ]
    },
];
