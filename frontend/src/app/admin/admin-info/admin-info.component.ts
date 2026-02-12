import { Component, OnInit } from '@angular/core';
import { AdminInfoService } from '../../services/admin-info.service';
import { CommonModule } from '@angular/common';
import { TranslocoPipe, TranslocoService } from '@jsverse/transloco';

@Component({
  selector: 'app-admin-info',
  templateUrl: './admin-info.component.html',
  imports: [CommonModule, TranslocoPipe],
  styleUrl: './admin-info.component.scss'
})
export class AdminInfoComponent implements OnInit {
  adminInfo: {
    username: string;
    name: string;
    surname: string;
    email: string;
    telephone: string;
    role: string;
    structures: Array<{ id: number; name: string }>;
  } | null = null;
  loading = true;
  error = '';

  constructor(
    private adminInfoService: AdminInfoService,
    private translocoService: TranslocoService
  ) { }

  ngOnInit(): void {
    this.adminInfoService.getAdminInfo().subscribe({
      next: (data) => {
        this.adminInfo = {
          username: data?.username || '',
          name: data?.name || '',
          surname: data?.surname || '',
          email: data?.email || '',
          telephone: data?.telephone || '',
          role: data?.role || '',
          structures: data?.structures || []
        };
        this.loading = false;
      },
      error: () => {
        this.error = this.translocoService.translate('admin-info-error');
        this.loading = false;
      }
    });
  }
}
