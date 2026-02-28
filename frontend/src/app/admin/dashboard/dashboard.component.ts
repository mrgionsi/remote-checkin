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
import { TranslocoService } from '@jsverse/transloco';
import { ButtonModule } from 'primeng/button';
import { SelectModule } from 'primeng/select';
import { FormsModule } from '@angular/forms';
import { CardModule } from 'primeng/card';
import { DialogModule } from 'primeng/dialog';
import { RouterLink } from '@angular/router';
import { ActivityService, ActivityItem, BackgroundJobItem } from '../../services/activity.service';
import { environment } from '../../../environments/environments';


@Component({
  selector: 'app-dashboard',
  imports: [ToastModule, IconFieldModule, InputIconModule, Toast, ChartModule, TableModule, InputTextModule, TagModule, CommonModule, TranslocoPipe, ButtonModule, SelectModule, FormsModule, CardModule, DialogModule, RouterLink],
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
  recentReservations: any[] = [];
  timelineItems: ActivityItem[] = [];
  recentJobs: BackgroundJobItem[] = [];
  healthItems: Array<{ label: string; value: number; tone: 'neutral' | 'warning' | 'success' }> = [];
  jobStatusFilter: string = '';
  jobTypeFilter: string = '';
  jobStatusOptions: Array<{ label: string; value: string }> = [];

  // Filter options
  statusOptions: Array<{ label: string; value: string }> = [];
  dateRangeOptions: Array<{ label: string; value: string }> = [];

  roomOptions: any[] = [];
  filteredReservations: any[] = [];

  // Loading and error states
  loadingReservations: boolean = false;
  loadingChart: boolean = false;
  loadingTimeline: boolean = false;
  loadingJobs: boolean = false;
  errorReservations: string | null = null;
  errorChart: string | null = null;
  errorJobs: string | null = null;

  // Keyboard shortcuts
  showShortcuts: boolean = false;

  private subscriptions: Subscription[] = [];
  private componentId = Math.random().toString(36).substr(2, 9);
  readonly enableJobsMonitor = environment.enableJobsMonitor;

  constructor(
    private reservationService: ReservationService,
    private router: Router,
    private authService: AuthService,
    @Inject(PLATFORM_ID) private platformId: object,
    private messageService: MessageService,
    private translocoService: TranslocoService,
    private activityService: ActivityService
  ) {

  }

  private setFilterOptions(): void {
    const keys = [
      'dashboard-filter-status-all',
      'dashboard-status-pending',
      'dashboard-status-approved',
      'dashboard-status-declined',
      'dashboard-status-sent-back',
      'dashboard-filter-date-all',
      'dashboard-date-today',
      'dashboard-date-week',
      'dashboard-date-month',
      'dashboard-jobs-filter-all-status',
      'dashboard-jobs-status-queued',
      'dashboard-jobs-status-running',
      'dashboard-jobs-status-retrying',
      'dashboard-jobs-status-succeeded',
      'dashboard-jobs-status-failed'
    ];

    const sub = this.translocoService.selectTranslateObject(keys).subscribe((translations: any) => {
      this.statusOptions = [
        { label: translations[0], value: '' },
        { label: translations[1], value: 'Pending' },
        { label: translations[2], value: 'Approved' },
        { label: translations[3], value: 'Declined' },
        { label: translations[4], value: 'Sent back to customer' }
      ];

      this.dateRangeOptions = [
        { label: translations[5], value: '' },
        { label: translations[6], value: 'today' },
        { label: translations[7], value: 'week' },
        { label: translations[8], value: 'month' }
      ];

      this.jobStatusOptions = [
        { label: translations[9], value: '' },
        { label: translations[10], value: 'queued' },
        { label: translations[11], value: 'running' },
        { label: translations[12], value: 'retrying' },
        { label: translations[13], value: 'succeeded' },
        { label: translations[14], value: 'failed' }
      ];
    });

    this.subscriptions.push(sub);
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

  getStatusLabelKey(status: string): string {
    switch (status) {
      case 'Pending':
        return 'dashboard-status-pending';
      case 'Approved':
        return 'dashboard-status-approved';
      case 'Declined':
        return 'dashboard-status-declined';
      case 'Sent back to customer':
        return 'dashboard-status-sent-back';
      default:
        return status;
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
    this.setFilterOptions();
    if (isPlatformBrowser(this.platformId)) {
      const structureId = this.getActiveStructureId();
      console.log('Selected structure ID resolved as:', structureId);
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
            this.updateInsights();
            this.loadingReservations = false;
          },
          error: (error) => {
            console.error('Error fetching reservations:', error);
            this.reservations = [];
            this.filteredReservations = [];
            this.loadingReservations = false;

            if (error.status === 404) {
              console.log('No reservations found for structure:', structureId);
              this.errorReservations = this.translocoService.translate('dashboard-error-no-reservations');
              this.messageService.add({
                severity: 'info',
                summary: this.translocoService.translate('dashboard-toast-no-reservations-title'),
                detail: this.translocoService.translate('dashboard-toast-no-reservations-detail'),
                life: 4000
              });
            } else {
              const errorMessage = this.getFriendlyReservationError(error);
              this.errorReservations = errorMessage;
              this.messageService.add({
                severity: 'error',
                summary: this.translocoService.translate('dashboard-toast-load-failed-title'),
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
        this.loadTimeline(structureId);
        if (this.enableJobsMonitor) {
          this.loadRecentJobs();
        }

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
            const errorMessage = this.getFriendlyChartError(error);
            this.errorChart = errorMessage;
            this.loadingChart = false;
            this.messageService.add({
              severity: 'error',
              summary: this.translocoService.translate('dashboard-toast-chart-load-failed-title'),
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
        this.handleNoStructureSelected();
        this.timelineItems = [];
        if (this.enableJobsMonitor) {
          this.loadRecentJobs();
        }
      }
    }
  }

  loadTimeline(structureId: number): void {
    this.loadingTimeline = true;
    const currentUserId = Number(this.authService.getUser()?.id || 0);
    const timelineSub = this.activityService.getRecentActivity(
      5,
      structureId,
      'administrator,admin,superadmin',
      1,
      currentUserId > 0 ? currentUserId : undefined
    ).subscribe({
      next: (response) => {
        this.timelineItems = response.items || [];
        this.loadingTimeline = false;
      },
      error: () => {
        this.timelineItems = [];
        this.loadingTimeline = false;
      }
    });
    this.subscriptions.push(timelineSub);
  }

  loadRecentJobs(): void {
    this.loadingJobs = true;
    this.errorJobs = null;
    const jobsSub = this.activityService.getRecentJobs(
      5,
      this.jobStatusFilter || undefined,
      this.jobTypeFilter || undefined,
      0
    ).subscribe({
      next: (response) => {
        this.recentJobs = response.items || [];
        this.loadingJobs = false;
      },
      error: (error) => {
        if (error?.status === 404) {
          this.recentJobs = [];
          this.errorJobs = null;
          this.loadingJobs = false;
          return;
        }
        this.recentJobs = [];
        this.loadingJobs = false;
        this.errorJobs = this.translocoService.translate('dashboard-jobs-error');
      }
    });
    this.subscriptions.push(jobsSub);
  }

  applyJobFilters(): void {
    this.loadRecentJobs();
  }

  clearJobFilters(): void {
    this.jobStatusFilter = '';
    this.jobTypeFilter = '';
    this.loadRecentJobs();
  }

  getJobStatusLabelKey(status: string): string {
    switch ((status || '').toLowerCase()) {
      case 'queued':
        return 'dashboard-jobs-status-queued';
      case 'running':
        return 'dashboard-jobs-status-running';
      case 'retrying':
        return 'dashboard-jobs-status-retrying';
      case 'succeeded':
        return 'dashboard-jobs-status-succeeded';
      case 'failed':
        return 'dashboard-jobs-status-failed';
      default:
        return status;
    }
  }

  getJobStatusSeverity(status: string): 'warn' | 'info' | 'success' | 'danger' | 'secondary' {
    switch ((status || '').toLowerCase()) {
      case 'queued':
        return 'secondary';
      case 'running':
      case 'retrying':
        return 'warn';
      case 'succeeded':
        return 'success';
      case 'failed':
        return 'danger';
      default:
        return 'info';
    }
  }

  getTimelineIcon(eventType: string): string {
    if (eventType.startsWith('reservation.')) return 'pi pi-calendar';
    if (eventType.startsWith('room.')) return 'pi pi-home';
    if (eventType.startsWith('structure.')) return 'pi pi-building';
    if (eventType.startsWith('user.')) return 'pi pi-user';
    if (eventType.startsWith('association.')) return 'pi pi-link';
    return 'pi pi-clock';
  }

  getTimelineWhen(isoDate: string): string {
    const eventDate = new Date(isoDate);
    if (isNaN(eventDate.getTime())) return '';
    const deltaMinutes = Math.max(0, Math.floor((Date.now() - eventDate.getTime()) / 60000));
    if (deltaMinutes < 1) return this.translocoService.translate('timeline-just-now');
    if (deltaMinutes < 60) return this.translocoService.translate('timeline-minutes-ago', { count: deltaMinutes });
    const deltaHours = Math.floor(deltaMinutes / 60);
    if (deltaHours < 24) return this.translocoService.translate('timeline-hours-ago', { count: deltaHours });
    const deltaDays = Math.floor(deltaHours / 24);
    return this.translocoService.translate('timeline-days-ago', { count: deltaDays });
  }

  getTimelineDescription(item: ActivityItem): string {
    const key = `timeline-event-${item.eventType.replaceAll('.', '-')}`;
    return this.translocoService.translate(key, item.metadata || {});
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
    this.updateInsights();
  }

  applyQuickFilter(type: string): void {
    switch (type) {
      case 'pending':
        this.statusFilter = 'Pending';
        this.dateRangeFilter = '';
        break;
      case 'approved':
        this.statusFilter = 'Approved';
        this.dateRangeFilter = '';
        break;
      case 'today':
        this.dateRangeFilter = 'today';
        break;
      case 'week':
        this.dateRangeFilter = 'week';
        break;
      default:
        break;
    }
    this.applyFilters();
  }

  clearQuickFilters(): void {
    this.statusFilter = '';
    this.dateRangeFilter = '';
    this.roomFilter = '';
    this.globalSearchTerm = '';
    this.applyFilters();
  }

  private updateInsights(): void {
    const source = this.filteredReservations;
    const sorted = [...source].sort((a: any, b: any) => {
      const aDate = new Date(a.start_date || a.end_date || 0).getTime();
      const bDate = new Date(b.start_date || b.end_date || 0).getTime();
      return bDate - aDate;
    });
    this.recentReservations = sorted.slice(0, 5);
    this.healthItems = [
      { label: 'dashboard-health-pending', value: this.summaryStats.pendingApprovals, tone: 'warning' },
      { label: 'dashboard-health-checkins', value: this.summaryStats.checkinsToday, tone: 'success' },
      { label: 'dashboard-health-checkouts', value: this.summaryStats.checkoutsToday, tone: 'neutral' }
    ];
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
    const structureId = this.getActiveStructureId();

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
          const errorMessage = this.getFriendlyReservationError(error);
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
          const errorMessage = this.getFriendlyChartError(error);
          this.errorChart = errorMessage;
          this.loadingChart = false;
        }
      });
      this.subscriptions.push(monthlySub);
    } else {
      this.handleNoStructureSelected();
    }
  }

  private getActiveStructureId(): number | null {
    const user = this.authService.getUser();
    const structures = Array.isArray(user?.structures) ? user.structures : [];
    if (structures.length === 0) {
      localStorage.removeItem('selected_structure_id');
      return null;
    }

    const structureIdStr = localStorage.getItem('selected_structure_id');
    const selectedStructureId = structureIdStr ? +structureIdStr : NaN;
    const isAllowed = structures.some((s: any) => s.id === selectedStructureId);
    if (isAllowed && selectedStructureId > 0) {
      return selectedStructureId;
    }

    const fallbackId = structures[0].id;
    localStorage.setItem('selected_structure_id', String(fallbackId));
    return fallbackId;
  }

  private handleNoStructureSelected(): void {
    this.reservations = [];
    this.filteredReservations = [];
    this.monthly_reservatvion = [];
    this.loadingReservations = false;
    this.loadingChart = false;
    this.errorReservations = this.translocoService.translate('dashboard-no-structure-error');
    this.errorChart = this.translocoService.translate('dashboard-no-structure-chart-error');
    this.messageService.add({
      severity: 'info',
      summary: this.translocoService.translate('dashboard-no-structure-title'),
      detail: this.translocoService.translate('dashboard-no-structure-detail'),
      life: 6000
    });
  }

  private getFriendlyReservationError(error: any): string {
    if (error?.status === 403) {
      return this.translocoService.translate('dashboard-error-structure-forbidden');
    }
    return error?.error?.message || error?.message || this.translocoService.translate('dashboard-error-load-reservations');
  }

  private getFriendlyChartError(error: any): string {
    if (error?.status === 403) {
      return this.translocoService.translate('dashboard-error-chart-forbidden');
    }
    return error?.error?.message || error?.message || this.translocoService.translate('dashboard-error-load-chart');
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
            summary: this.translocoService.translate('dashboard-toast-shortcut-title'),
            detail: this.translocoService.translate('dashboard-toast-shortcut-pending'),
            life: 2000
          });
          break;
        case 'f':
          event.preventDefault();
          this.clearFilters();
          this.messageService.add({
            severity: 'info',
            summary: this.translocoService.translate('dashboard-toast-shortcut-title'),
            detail: this.translocoService.translate('dashboard-toast-shortcut-clear'),
            life: 2000
          });
          break;
        case 'r':
          event.preventDefault();
          this.retryLoadData();
          this.messageService.add({
            severity: 'info',
            summary: this.translocoService.translate('dashboard-toast-shortcut-title'),
            detail: this.translocoService.translate('dashboard-toast-shortcut-retry'),
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
