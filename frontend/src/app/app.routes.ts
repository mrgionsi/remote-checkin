import { Routes } from '@angular/router';
import { LanguageComponent } from './language/language.component';
import { RemoteCheckinComponent } from './remote-checkin/remote-checkin.component';
import { DashboardComponent } from './admin/dashboard/dashboard.component';
import { CreateReservationComponent } from './admin/create-reservation/create-reservation.component';
import { AdminHomeComponent } from './admin/admin-home/admin-home.component';

export const routes: Routes = [
    { path: '', component: LanguageComponent },
    { path: 'remote-checkin/:code', component: RemoteCheckinComponent }, // Dynamic route
    {
        path: 'admin',
        component: AdminHomeComponent, // Acts as the parent
        children: [
            { path: 'dashboard', component: DashboardComponent },
            { path: 'create-reservation', component: CreateReservationComponent },
            { path: '', redirectTo: 'dashboard', pathMatch: 'full' },

        ]
    },
];
