import { Component, OnInit } from '@angular/core';
import { AdminInfoService } from '../../services/admin-info.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-admin-info',
  templateUrl: './admin-info.component.html',
  imports: [CommonModule],
  styleUrl: './admin-info.component.scss'
})
export class AdminInfoComponent implements OnInit {
  adminInfo: any = null;
  loading = true;
  error: string | null = null;

  constructor(private adminInfoService: AdminInfoService) { }

  ngOnInit(): void {
    this.adminInfoService.getAdminInfo().subscribe({
      next: (data) => {
        this.adminInfo = data;
        this.loading = false;
      },
      error: () => {
        this.error = 'Errore nel recupero delle informazioni utente';
        this.loading = false;
      }
    });
  }
}
