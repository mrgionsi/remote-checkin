import { CommonModule, isPlatformBrowser } from '@angular/common';
import { Component, OnInit, OnDestroy, Inject, PLATFORM_ID, HostListener } from '@angular/core';
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
import { CardModule } from 'primeng/card';
import { DialogModule } from 'primeng/dialog';
import { ProgressSpinnerModule } from 'primeng/progressspinner';


@Component({
  selector: 'app-dashboard',
  imports: [ToastModule, IconFieldModule, InputIconModule, Toast, ChartModule, TableModule, InputTextModule, TagModule, CommonModule, TranslocoPipe, ButtonModule, SelectModule, FormsModule, CardModule, DialogModule, ProgressSpinnerModule],
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
    { label: 'Bar Chart', value: 'bar' }
  ];

  // Summary statistics
  summaryStats = {
    totalReservations: 0,
    pendingApprovals: 0,
    checkinsToday: 0,
    checkoutsToday: 0
  };

  // Table filters
  statusFilter: string = '';
  dateRangeFilter: string = '';
  roomFilter: string = '';
  globalSearchTerm: string = '';

  // Filter options
  statusOptions = [
    { label: 'All Status', value: '' },
    { label: 'Pending', value: 'Pending' },
    { label: 'Approved', value: 'Approved' },
    { label: 'Declined', value: 'Declined' },
    { label: 'Sent back to customer', value: 'Sent back to customer' }
  ];

  dateRangeOptions = [
    { label: 'All Dates', value: '' },
    { label: 'Today', value: 'today' },
    { label: 'This Week', value: 'week' },
    { label: 'This Month', value: 'month' }
  ];

  roomOptions: any[] = [];
  filteredReservations: any[] = [];

  // Loading and error states
  loadingReservations: boolean = false;
  loadingChart: boolean = false;
  errorReservations: string | null = null;
  errorChart: string | null = null;

  // Keyboard shortcuts
  showShortcuts: boolean = false;

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
        this.loadingReservations = true;
        this.errorReservations = null;

        const reservationSub = this.reservationService.getReservationByStructureId(structureId).subscribe({
          next: (reservations) => {
            console.log('Reservations received:', reservations);
            this.reservations = reservations || [];
            this.filteredReservations = [...this.reservations];
            this.calculateSummaryStats();
            this.extractRoomOptions();
            this.loadingReservations = false;
          },
          error: (error) => {
            console.error('Error fetching reservations:', error);
            this.reservations = [];
            this.filteredReservations = [];
            this.loadingReservations = false;

            if (error.status === 404) {
              console.log('No reservations found for structure:', structureId);
              this.errorReservations = 'No reservations found for this structure';
              this.messageService.add({
                severity: 'info',
                summary: 'No Reservations',
                detail: 'No reservations found for this structure',
                life: 4000
              });
            } else {
              const errorMessage = error?.error?.message || error?.message || 'Failed to load reservations. Please try again.';
              this.errorReservations = errorMessage;
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
        this.loadingChart = true;
        this.errorChart = null;

        const monthlySub = this.reservationService.getMonthlyReservation(structureId).subscribe({
          next: (monthly_reserv) => {
            console.log('Reservations:', monthly_reserv);
            // Handle the response data here
            this.monthly_reservatvion = monthly_reserv.map((item: { total_reservations: any; }) => item.total_reservations);
            this.updateChartData();
            this.loadingChart = false;
          },
          error: (error) => {
            console.error('Error fetching monthly reservations:', error);
            const errorMessage = error?.error?.message || error?.message || 'Failed to load monthly reservations chart. Please try again.';
            this.errorChart = errorMessage;
            this.loadingChart = false;
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
    const isLineChart = this.selectedChartType === 'line';

    this.checkInData = {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
      datasets: [
        {
          label: 'Check-ins',
          data: this.monthly_reservatvion,
          fill: false,
          borderColor: '#42A5F5',
          backgroundColor: isLineChart ? 'rgba(66, 165, 245, 0.1)' : 'rgba(66, 165, 245, 0.8)',
          borderWidth: 3,
          pointBackgroundColor: '#42A5F5',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 8,
          tension: 0.4
        }
      ]
    };

    // Calculate max value for proper y-axis scaling
    const maxValue = Math.max(...this.monthly_reservatvion);
    const suggestedMax = Math.max(maxValue + 1, 5); // Ensure at least 5 for better visibility

    this.chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            usePointStyle: true,
            padding: 20,
            font: {
              size: 14,
              weight: 500
            }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#ffffff',
          bodyColor: '#ffffff',
          borderColor: '#42A5F5',
          borderWidth: 1,
          cornerRadius: 8,
          displayColors: true,
          padding: 12
        }
      },
      scales: {
        x: {
          title: {
            display: true,
            text: 'Month',
            font: {
              size: 14,
              weight: 600
            },
            color: '#374151'
          },
          grid: {
            display: false
          },
          ticks: {
            font: {
              size: 12
            },
            color: '#6B7280'
          }
        },
        y: {
          title: {
            display: true,
            text: 'Number of Check-ins',
            font: {
              size: 14,
              weight: 600
            },
            color: '#374151'
          },
          beginAtZero: true,
          max: suggestedMax,
          ticks: {
            stepSize: 1,
            precision: 0,
            font: {
              size: 12
            },
            color: '#6B7280'
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.04)'
          }
        }
      }
    };
  }

  onChartTypeChange(): void {
    this.updateChartData();
  }

  get chartType(): 'line' | 'bar' {
    return this.selectedChartType as 'line' | 'bar';
  }

  calculateSummaryStats(): void {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const todayStr = today.toISOString().split('T')[0];

    this.summaryStats = {
      totalReservations: this.reservations.length,
      pendingApprovals: this.reservations.filter((r: any) => r.status === 'Pending').length,
      checkinsToday: this.reservations.filter((r: any) => {
        const startDate = new Date(r.start_date);
        startDate.setHours(0, 0, 0, 0);
        return startDate.toISOString().split('T')[0] === todayStr;
      }).length,
      checkoutsToday: this.reservations.filter((r: any) => {
        const endDate = new Date(r.end_date);
        endDate.setHours(0, 0, 0, 0);
        return endDate.toISOString().split('T')[0] === todayStr;
      }).length
    };
  }

  extractRoomOptions(): void {
    const uniqueRooms = [...new Set(this.reservations.map((r: any) => r.room_name))];
    this.roomOptions = [
      { label: 'All Rooms', value: '' },
      ...uniqueRooms.map(room => ({ label: room, value: room }))
    ];
  }

  applyFilters(): void {
    let filtered = [...this.reservations];

    // Status filter
    if (this.statusFilter) {
      filtered = filtered.filter((r: any) => r.status === this.statusFilter);
    }

    // Date range filter
    if (this.dateRangeFilter) {
      const today = new Date();
      const todayStr = today.toISOString().split('T')[0];

      filtered = filtered.filter((r: any) => {
        const startDate = new Date(r.start_date);
        const startDateStr = startDate.toISOString().split('T')[0];

        switch (this.dateRangeFilter) {
          case 'today':
            return startDateStr === todayStr;
          case 'week':
            const weekAgo = new Date(today);
            weekAgo.setDate(today.getDate() - 7);
            return startDate >= weekAgo;
          case 'month':
            const monthAgo = new Date(today);
            monthAgo.setMonth(today.getMonth() - 1);
            return startDate >= monthAgo;
          default:
            return true;
        }
      });
    }

    // Room filter
    if (this.roomFilter) {
      filtered = filtered.filter((r: any) => r.room_name === this.roomFilter);
    }

    // Global search
    if (this.globalSearchTerm) {
      const searchTerm = this.globalSearchTerm.toLowerCase();
      filtered = filtered.filter((r: any) =>
        r.id_reference?.toLowerCase().includes(searchTerm) ||
        r.name_reference?.toLowerCase().includes(searchTerm) ||
        r.room_name?.toLowerCase().includes(searchTerm) ||
        r.status?.toLowerCase().includes(searchTerm)
      );
    }

    this.filteredReservations = filtered;
  }

  onFilterChange(): void {
    this.applyFilters();
  }

  onGlobalSearch(event: any): void {
    this.globalSearchTerm = event.target.value;
    this.applyFilters();
  }

  clearFilters(): void {
    this.statusFilter = '';
    this.dateRangeFilter = '';
    this.roomFilter = '';
    this.globalSearchTerm = '';
    this.applyFilters();
  }

  filterPendingApprovals(): void {
    this.statusFilter = 'Pending';
    this.dateRangeFilter = '';
    this.roomFilter = '';
    this.globalSearchTerm = '';
    this.applyFilters();
  }

  retryLoadData(): void {
    const structureIdStr = localStorage.getItem('selected_structure_id');
    const structureId = structureIdStr ? +structureIdStr : null;

    if (structureId && !isNaN(structureId) && structureId > 0) {
      // Retry reservations
      this.loadingReservations = true;
      this.errorReservations = null;

      const reservationSub = this.reservationService.getReservationByStructureId(structureId).subscribe({
        next: (reservations) => {
          this.reservations = reservations || [];
          this.filteredReservations = [...this.reservations];
          this.calculateSummaryStats();
          this.extractRoomOptions();
          this.loadingReservations = false;
        },
        error: (error) => {
          this.reservations = [];
          this.filteredReservations = [];
          this.loadingReservations = false;
          const errorMessage = error?.error?.message || error?.message || 'Failed to load reservations. Please try again.';
          this.errorReservations = errorMessage;
        }
      });
      this.subscriptions.push(reservationSub);

      // Retry chart
      this.loadingChart = true;
      this.errorChart = null;

      const monthlySub = this.reservationService.getMonthlyReservation(structureId).subscribe({
        next: (monthly_reserv) => {
          this.monthly_reservatvion = monthly_reserv.map((item: { total_reservations: any; }) => item.total_reservations);
          this.updateChartData();
          this.loadingChart = false;
        },
        error: (error) => {
          const errorMessage = error?.error?.message || error?.message || 'Failed to load monthly reservations chart. Please try again.';
          this.errorChart = errorMessage;
          this.loadingChart = false;
        }
      });
      this.subscriptions.push(monthlySub);
    }
  }

  @HostListener('document:keydown', ['$event'])
  handleKeyboardEvent(event: KeyboardEvent): void {
    // Don't trigger shortcuts when user is typing in input fields
    const target = event.target as HTMLElement;
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.contentEditable === 'true') {
      return;
    }

    // Handle keyboard shortcuts
    if (event.ctrlKey || event.metaKey) {
      switch (event.key.toLowerCase()) {
        case 'p':
          event.preventDefault();
          this.filterPendingApprovals();
          this.messageService.add({
            severity: 'info',
            summary: 'Keyboard Shortcut',
            detail: 'Filtered to pending approvals',
            life: 2000
          });
          break;
        case 'f':
          event.preventDefault();
          this.clearFilters();
          this.messageService.add({
            severity: 'info',
            summary: 'Keyboard Shortcut',
            detail: 'Cleared all filters',
            life: 2000
          });
          break;
        case 'r':
          event.preventDefault();
          this.retryLoadData();
          this.messageService.add({
            severity: 'info',
            summary: 'Keyboard Shortcut',
            detail: 'Retrying data load',
            life: 2000
          });
          break;
        case '/':
          event.preventDefault();
          this.showShortcuts = !this.showShortcuts;
          break;
      }
    }

    // Handle single key shortcuts
    switch (event.key.toLowerCase()) {
      case 'escape':
        this.showShortcuts = false;
        break;
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

