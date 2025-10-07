import { CommonModule, isPlatformBrowser } from '@angular/common';
import { Component, OnInit, OnDestroy, Inject, PLATFORM_ID } from '@angular/core';
import { Subscription } from 'rxjs';
import { InputTextModule } from 'primeng/inputtext';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ChartModule } from 'primeng/chart';
import { ChartOptions } from 'chart.js';
import { Toast, ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { ReservationService } from '../../services/reservation.service';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { TranslocoPipe } from '@jsverse/transloco';


@Component({
  selector: 'app-dashboard',
  imports: [ToastModule, IconFieldModule, InputIconModule, Toast, ChartModule, TableModule, InputTextModule, TagModule, CommonModule, TranslocoPipe],
  providers: [MessageService],
  host: { ngSkipHydration: 'true' },
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit, OnDestroy {
  options: any;

  // Example remote check-ins data
  reservations: any[] = [];
  monthly_reservatvion: any[] = [];
  searchTerm: any;
  reservationData: any;
  checkInData: any;
  chartOptions: ChartOptions | undefined;

  private subscriptions: Subscription[] = [];
  private componentId = Math.random().toString(36).substr(2, 9);

  constructor(
    private reservationService: ReservationService,
    private router: Router,
    private authService: AuthService,
    @Inject(PLATFORM_ID) private platformId: object,

  ) {

  }

  getStatusSeverity(status: string) {
    switch (status) {
      case 'Approved':
        return 'success';
      case 'Pending':
        return 'warn'; // You can also use 'info' or 'secondary', depending on your use case
      case 'Declined':
        return 'danger'; // You can also use 'info' or 'secondary', depending on your use case
      case 'Sent back to customer':
        return 'warn'; // You can also use 'info' or 'secondary', depending on your use case
      default:
        return 'info'; // Default severity if status doesn't match
    }
  }



  navigateToDetails(event: any): void {
    const reservation = event.data;  // 'data' contains the selected row object
    console.log(reservation)
    if (reservation?.reservation_id) {
      this.router.navigate([`/admin/reservation-details/${reservation.reservation_id}`]);
    }
  }

  ngOnInit(): void {
    console.log('DashboardComponent initialized with ID:', this.componentId);
    if (isPlatformBrowser(this.platformId)) {
      const structureIdStr = localStorage.getItem('selected_structure_id');
      const structureId = structureIdStr ? +structureIdStr : null;
      console.log('Selected structure ID from localStorage:', structureIdStr, 'Parsed as:', structureId);
      if (structureId && !isNaN(structureId) && structureId > 0) {
        // Subscribe to reservations and store subscription
        const reservationSub = this.reservationService.getReservationByStructureId(structureId).subscribe({
          next: (reservations) => {
            console.log('Reservations received:', reservations);
            this.reservations = reservations || [];
          },
          error: (error) => {
            console.error('Error fetching reservations:', error);
            this.reservations = [];
            // Show error message to user
            if (error.status === 404) {
              console.log('No reservations found for structure:', structureId);
            }
          },
          complete: () => {
            console.log('Reservation fetch completed for structure:', structureId);
          }
        });
        this.subscriptions.push(reservationSub);

        // Subscribe to monthly reservations and store subscription
        const monthlySub = this.reservationService.getMonthlyReservation(structureId).subscribe({
          next: (monthly_reserv) => {
            console.log('Reservations:', monthly_reserv);
            // Handle the response data here
            this.monthly_reservatvion = monthly_reserv.map((item: { total_reservations: any; }) => item.total_reservations);
            this.checkInData = {
              labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'August', 'Sept', 'Oct', 'Nov', 'Dec'], // Example months
              datasets: [
                {
                  label: 'Check-ins',
                  data: this.monthly_reservatvion,
                  fill: true,
                  borderColor: '#42A5F5',
                  tension: 0.1
                }
              ]
            };

            this.chartOptions = {
              responsive: true,
              scales: {
                x: { title: { display: true, text: 'Month' } },
                y: { title: { display: true, text: 'Check-ins' } }
              }
            };
          },
          error: (error) => {
            console.error('Error fetching reservations:', error);
            // Handle the error here (e.g., show a message to the user)
          },
          complete: () => {
            console.log('Reservation fetch completed.');
            // Optional: Handle completion logic
          }
        });
        this.subscriptions.push(monthlySub);
      } else {
        console.log('No valid structure ID found. Structure ID:', structureId);
        console.log('localStorage selected_structure_id:', localStorage.getItem('selected_structure_id'));
       } else {
         console.log('No valid structure ID found. Structure ID:', structureId);
         console.log('localStorage selected_structure_id:', localStorage.getItem('selected_structure_id'));
       }
      }
    }
  }

  ngOnDestroy(): void {
    // Clean up all subscriptions to prevent memory leaks and duplicate calls
    this.subscriptions.forEach(sub => {
      if (sub && !sub.closed) {
        sub.unsubscribe();
      }
    });
    this.subscriptions = [];
    console.log('DashboardComponent destroyed with ID:', this.componentId, '- subscriptions cleaned up');
  }
}


