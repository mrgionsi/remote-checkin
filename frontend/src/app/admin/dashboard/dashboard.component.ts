import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { InputTextModule } from 'primeng/inputtext';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ChartModule } from 'primeng/chart';
import { ChartOptions } from 'chart.js';


@Component({
  selector: 'app-dashboard',
  imports: [ChartModule, TableModule, InputTextModule, TagModule, CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit {
  options: any;

  // Example remote check-ins data
  checkIns: any[] = [
    {
      reservationNumber: '12345',
      guestName: 'John Doe',
      room: 'SPA',
      checkInDate: new Date('2025-02-01T10:00:00'),
      status: 'Completed'
    },
    {
      reservationNumber: '12346',
      guestName: 'Jane Smith',
      room: 'Giungla',
      checkInDate: new Date('2025-02-02T12:00:00'),
      status: 'Pending'
    },
    // Add more check-ins as needed
  ];

  searchTerm: any;

  constructor() { }


  getStatusSeverity(status: string) {
    switch (status) {
      case 'Completed':
        return 'success';
      case 'Pending':
        return 'warn'; // You can also use 'info' or 'secondary', depending on your use case
      default:
        return 'info'; // Default severity if status doesn't match
    }
  }


  checkInData: any;
  chartOptions: ChartOptions | undefined;

  ngOnInit(): void {

    this.checkInData = {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'], // Example months
      datasets: [
        {
          label: 'Check-ins',
          data: [5, 10, 7, 15, 12], // Example check-ins data
          fill: false,
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
  }

}