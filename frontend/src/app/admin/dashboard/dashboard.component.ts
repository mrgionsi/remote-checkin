import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
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


@Component({
  selector: 'app-dashboard',
  imports: [ToastModule, IconFieldModule, InputIconModule, Toast, ChartModule, TableModule, InputTextModule, TagModule, CommonModule],
  providers: [MessageService],
  host: { ngSkipHydration: 'true' },
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit {
  options: any;

  // Example remote check-ins data
  reservations: any[] = [];
  monthly_reservatvion: any[] = [];
  searchTerm: any;

  constructor(private messageService: MessageService,
    private reservationService: ReservationService
  ) {

  }

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

  reservationData: any;
  checkInData: any;
  chartOptions: ChartOptions | undefined;

  ngOnInit(): void {

    this.messageService.add({ severity: 'info', summary: 'Info', detail: 'Message Content' });
    this.reservationService.getReservationByStructureId(1).subscribe({
      next: (reservations) => {
        console.log('Reservations:', reservations);
        this.reservations = reservations;
        // Handle the response data here
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
    this.reservationService.getMonthlyReservation(1).subscribe({
      next: (monthly_reserv) => {
        console.log('Reservations:', monthly_reserv);
        // Handle the response data here
        this.monthly_reservatvion = monthly_reserv.map((item: { total_reservations: any; }) => item.total_reservations);
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
  }

}

function ViewChild(arg0: string): (target: DashboardComponent, propertyKey: "dt") => void {
  throw new Error('Function not implemented.');
}
