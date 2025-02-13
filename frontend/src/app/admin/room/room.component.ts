import { AfterViewInit, Component } from '@angular/core';
import { TableModule } from 'primeng/table';
import { ConfirmationService } from 'primeng/api';
import { RoomService } from '../../services/room.service';
import { DialogModule } from 'primeng/dialog'; // Import DialogModule
import { ConfirmDialogModule } from 'primeng/confirmdialog'; // Import DialogModule

import { ButtonModule } from 'primeng/button'; // Required for buttons in the dialog
import { InputTextModule } from 'primeng/inputtext'; // Required for input fields
import { FormsModule } from '@angular/forms'; // Required for [(ngModel)]


@Component({
  selector: 'app-room',
  imports: [TableModule, DialogModule,
    ButtonModule,
    InputTextModule,
    ConfirmDialogModule,
    FormsModule],
  templateUrl: './room.component.html',
  styleUrl: './room.component.scss',
  providers: [ConfirmationService]
})
export class RoomComponent implements AfterViewInit {

  constructor(private confirmationService: ConfirmationService,
    private roomService: RoomService) { }
  rooms: any;
  editDialogVisible = false;
  selectedRoom: any = {};
  ngAfterViewInit(): void {
    this.roomService.getRooms().subscribe({
      next: (value) => {
        console.log(value)
        this.rooms = value
      }
    }
    )
  }
  editRoom(room: any) {
    this.selectedRoom = { ...room }; // Clone object to avoid modifying original data before save
    this.editDialogVisible = true;
  }

  saveEdit() {
    const index = this.rooms.findIndex((r: any) => r.id === this.selectedRoom.id);
    if (index !== -1) {
      this.rooms[index] = { ...this.selectedRoom };
    }
    this.editDialogVisible = false;
  }

  confirmDelete(room: any) {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete ${room.name}?`,
      header: 'Confirm Deletion',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.rooms = this.rooms.filter((r: any) => r.id !== room.id);
      }
    });
  }
}
