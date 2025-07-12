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
import { AuthGuard } from './guards/auth.guard';
import { AdminInfoComponent } from './admin/admin-info/admin-info.component';

export const routes: Routes = [
    { path: '', component: LanguageComponent },
    { path: ':id', component: LanguageComponent }, // Optional reservation ID in language selection
    { path: 'reservation-check/:code', component: ReservationCheckComponent }, // Check reservation
    { path: ':id/remote-checkin/:code', component: RemoteCheckinComponent }, // Dynamic check-in with reservation ID
    { path: 'remote-checkin/:code', redirectTo: 'reservation-check/:code', pathMatch: 'full' }, // Redirect if no ID
    { path: 'admin', redirectTo: 'admin/dashboard', pathMatch: 'full' }, // Add this redirect

    {
        path: 'admin',
        component: AdminHomeComponent, // Acts as the parent,
        children: [
            { path: 'login', component: LoginComponent },
            { path: 'dashboard', component: DashboardComponent, canActivate: [AuthGuard] },
            { path: 'rooms', component: RoomComponent, canActivate: [AuthGuard] },
            { path: 'reservation-details/:id_reservation', component: DetailReservationComponent, canActivate: [AuthGuard] },
            { path: 'create-reservation', component: CreateReservationComponent, canActivate: [AuthGuard] },
            { path: 'admin-info', component: AdminInfoComponent, canActivate: [AuthGuard] }, // <--- aggiungi questa riga
            { path: '', redirectTo: 'dashboard', pathMatch: 'full' },

        ]
    },
];
