import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TranslocoPipe, TranslocoService } from '@jsverse/transloco';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { Subscription } from 'rxjs';
import { ActivityService, BackgroundJobItem } from '../../services/activity.service';

@Component({
  selector: 'app-jobs-monitor',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslocoPipe, TagModule, ButtonModule],
  templateUrl: './jobs-monitor.component.html',
  styleUrl: './jobs-monitor.component.scss'
})
export class JobsMonitorComponent implements OnInit, OnDestroy {
  items: BackgroundJobItem[] = [];
  loading = false;
  error: string | null = null;
  statusFilter = '';
  jobTypeFilter = '';
  limit = 20;
  offset = 0;
  total = 0;
  readonly statusOptions = ['queued', 'running', 'retrying', 'succeeded', 'failed'];

  private readonly subscriptions: Subscription[] = [];

  constructor(
    private readonly activityService: ActivityService,
    private readonly translocoService: TranslocoService
  ) {}

  ngOnInit(): void {
    this.loadJobs(true);
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach((sub) => sub.unsubscribe());
  }

  loadJobs(resetOffset = false): void {
    if (resetOffset) {
      this.offset = 0;
    }

    this.loading = true;
    this.error = null;
    const sub = this.activityService.getRecentJobs(
      this.limit,
      this.statusFilter || undefined,
      this.jobTypeFilter || undefined,
      this.offset
    ).subscribe({
      next: (response) => {
        this.items = response.items || [];
        this.total = Number(response.pagination?.total || 0);
        this.loading = false;
      },
      error: (error) => {
        if (error?.status === 404) {
          this.items = [];
          this.total = 0;
          this.error = null;
          this.loading = false;
          return;
        }
        this.items = [];
        this.error = this.translocoService.translate('dashboard-jobs-error');
        this.loading = false;
      }
    });
    this.subscriptions.push(sub);
  }

  applyFilters(): void {
    this.loadJobs(true);
  }

  clearFilters(): void {
    this.statusFilter = '';
    this.jobTypeFilter = '';
    this.loadJobs(true);
  }

  nextPage(): void {
    if (this.offset + this.limit >= this.total) {
      return;
    }
    this.offset += this.limit;
    this.loadJobs(false);
  }

  previousPage(): void {
    if (this.offset === 0) {
      return;
    }
    this.offset = Math.max(0, this.offset - this.limit);
    this.loadJobs(false);
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
}
