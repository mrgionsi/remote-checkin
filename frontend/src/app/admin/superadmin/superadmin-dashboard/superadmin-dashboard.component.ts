import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { SuperadminService, DashboardData } from '../../../services/superadmin.service';
import { TranslocoPipe, TranslocoService } from '@jsverse/transloco';
import { ActivityItem, ActivityService, BackgroundJobItem } from '../../../services/activity.service';
import { FormsModule } from '@angular/forms';
import { environment } from '../../../../environments/environments';

@Component({
  selector: 'app-superadmin-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslocoPipe, FormsModule],
  templateUrl: './superadmin-dashboard.component.html',
  styleUrls: ['./superadmin-dashboard.component.scss']
})
export class SuperadminDashboardComponent implements OnInit {
  dashboardData: DashboardData | null = null;
  timelineItems: ActivityItem[] = [];
  recentJobs: BackgroundJobItem[] = [];
  loading = true;
  loadingTimeline = true;
  loadingJobs = true;
  error: string | null = null;
  errorJobs: string | null = null;
  jobStatusFilter = '';
  jobTypeFilter = '';
  readonly enableJobsMonitor = environment.enableJobsMonitor;

  constructor(
    private superadminService: SuperadminService,
    private translocoService: TranslocoService,
    private activityService: ActivityService
  ) { }

  ngOnInit(): void {
    this.loadDashboardData();
  }

  loadDashboardData(): void {
    this.loading = true;
    this.error = null;

    this.superadminService.getDashboardData().subscribe({
      next: (response) => {
        this.dashboardData = response.dashboard;
        this.loading = false;
        this.loadTimeline();
        if (this.enableJobsMonitor) {
          this.loadRecentJobs();
        }
      },
      error: (error) => {
        this.error = error.message || 'Failed to load dashboard data';
        this.loading = false;
      }
    });
  }

  loadTimeline(): void {
    this.loadingTimeline = true;
    this.superadminService.getActivityTimeline(5).subscribe({
      next: (response) => {
        this.timelineItems = response.items || [];
        this.loadingTimeline = false;
      },
      error: () => {
        this.timelineItems = [];
        this.loadingTimeline = false;
      }
    });
  }

  loadRecentJobs(): void {
    this.loadingJobs = true;
    this.errorJobs = null;
    this.activityService.getRecentJobs(
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
        this.errorJobs = this.translocoService.translate('dashboard-jobs-error');
        this.loadingJobs = false;
      }
    });
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

  getTimelineDescription(item: ActivityItem): string {
    const key = `timeline-event-${item.eventType.replaceAll('.', '-')}`;
    return this.translocoService.translate(key, item.metadata || {});
  }
}
