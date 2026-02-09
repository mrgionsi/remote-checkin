import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { SuperadminService, DashboardData } from '../../../services/superadmin.service';

@Component({
  selector: 'app-superadmin-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './superadmin-dashboard.component.html',
  styleUrls: ['./superadmin-dashboard.component.scss']
})
export class SuperadminDashboardComponent implements OnInit {
  dashboardData: DashboardData | null = null;
  loading = true;
  error: string | null = null;

  constructor(private superadminService: SuperadminService) { }

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
      },
      error: (error) => {
        this.error = error.message || 'Failed to load dashboard data';
        this.loading = false;
      }
    });
  }
}
