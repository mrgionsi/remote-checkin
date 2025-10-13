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
import { ButtonModule } from 'primeng/button';
import { SelectModule } from 'primeng/select';
import { FormsModule } from '@angular/forms';


@Component({
  selector: 'app-dashboard',
  imports: [ToastModule, IconFieldModule, InputIconModule, Toast, ChartModule, TableModule, InputTextModule, TagModule, CommonModule, TranslocoPipe, ButtonModule, SelectModule, FormsModule],
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

  // Chart enhancement properties
  selectedChartType: string = 'line';
  chartTypeOptions = [
    { label: 'Line Chart', value: 'line' },
    { label: 'Bar Chart', value: 'bar' },
    { label: 'Area Chart', value: 'area' }
  ];

  private subscriptions: Subscription[] = [];
  private componentId = Math.random().toString(36).substr(2, 9);

  constructor(
    private reservationService: ReservationService,
    private router: Router,
    private authService: AuthService,
    @Inject(PLATFORM_ID) private platformId: object,
    private messageService: MessageService
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

            if (error.status === 404) {
              console.log('No reservations found for structure:', structureId);
              this.messageService.add({
                severity: 'info',
                summary: 'No Reservations',
                detail: 'No reservations found for this structure',
                life: 4000
              });
            } else {
              const errorMessage = error?.error?.message || error?.message || 'Failed to load reservations. Please try again.';
              this.messageService.add({
                severity: 'error',
                summary: 'Reservations load failed',
                detail: errorMessage,
                life: 6000
              });
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
            this.updateChartData();
          },
          error: (error) => {
            console.error('Error fetching monthly reservations:', error);
            const errorMessage = error?.error?.message || error?.message || 'Failed to load monthly reservations chart. Please try again.';
            this.messageService.add({
              severity: 'error',
              summary: 'Chart load failed',
              detail: errorMessage,
              life: 6000
            });
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
      }
    }
  }

  updateChartData(): void {
    const isFilled = this.selectedChartType === 'area';
    
    this.checkInData = {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
      datasets: [
        {
          label: 'Check-ins',
          data: this.monthly_reservatvion,
          fill: isFilled,
          borderColor: '#42A5F5',
          backgroundColor: isFilled ? 'rgba(66, 165, 245, 0.2)' : 'rgba(66, 165, 245, 0.8)',
          tension: 0.4
        }
      ]
    };

    this.chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top'
        },
        tooltip: {
          mode: 'index',
          intersect: false
        }
      },
      scales: {
        x: { 
          title: { 
            display: true, 
            text: 'Month' 
          },
          grid: {
            display: false
          }
        },
        y: { 
          title: { 
            display: true, 
            text: 'Number of Check-ins' 
          },
          beginAtZero: true,
          ticks: {
            stepSize: 1,
            precision: 0
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          }
        }
      }
    };
  }

  onChartTypeChange(): void {
    this.updateChartData();
  }

  get chartType(): 'line' | 'bar' {
    return this.selectedChartType === 'area' ? 'line' : (this.selectedChartType as 'line' | 'bar');
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

