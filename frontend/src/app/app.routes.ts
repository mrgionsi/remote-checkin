import { Routes } from '@angular/router';
import { LanguageComponent } from './language/language.component';
import { RemoteCheckinComponent } from './remote-checkin/remote-checkin.component';
import { DashboardComponent } from './admin/dashboard/dashboard.component';
import { CreateReservationComponent } from './admin/create-reservation/create-reservation.component';
import { AdminHomeComponent } from './admin/admin-home/admin-home.component';
import { RoomComponent } from './admin/room/room.component';
import { ReservationCheckComponent } from './reservation-check/reservation-check.component';
import { DetailReservationComponent } from './detail-reservation/detail-reservation.component';

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
            { path: 'dashboard', component: DashboardComponent },
            { path: 'rooms', component: RoomComponent },
            { path: 'reservation-details/:id_reservation', component: DetailReservationComponent },
            { path: 'create-reservation', component: CreateReservationComponent },
            { path: '', redirectTo: 'dashboard', pathMatch: 'full' },

        ]
    },
];
