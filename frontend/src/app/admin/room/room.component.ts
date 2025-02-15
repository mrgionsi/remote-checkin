import { Component, OnInit } from '@angular/core';
import { TableModule } from 'primeng/table';
import { RoomService } from '../../services/room.service';
import { DialogModule } from 'primeng/dialog';
import { ConfirmationService, MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button'; // Required for buttons in the dialog
import { InputTextModule } from 'primeng/inputtext'; // Required for input fields
import { FormsModule } from '@angular/forms'; // Required for [(ngModel)]
import { CommonModule } from '@angular/common';
import { ToastModule } from 'primeng/toast';
import { TagModule } from 'primeng/tag';
import { SelectModule } from 'primeng/select';
import { ConfirmDialogModule } from 'primeng/confirmdialog';


@Component({
  selector: 'app-room',
  imports: [TableModule, DialogModule,
    ButtonModule,
    InputTextModule,
    SelectModule,
    TagModule,
    CommonModule,
    ToastModule,
    ConfirmDialogModule,
    FormsModule],
  templateUrl: './room.component.html',
  styleUrl: './room.component.scss',
  providers: [MessageService, ConfirmationService]
})
export class RoomComponent implements OnInit {

  constructor(private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private roomService: RoomService) { }

  clonedProducts: { [s: string]: any } = {};

  rooms: any;
  editDialogVisible = false;
  selectedRoom: any = {};
  ngOnInit(): void {
    this.roomService.getRooms().subscribe({
      next: (value) => {
        console.log(value)
        this.rooms = value
      }
    }
    )
  }
  onRowEditInit(room: any) {
    this.clonedProducts[room.id as string] = { ...room };
  }

  onRowEditSave(room: any) {

  }

  onRowEditCancel(room: any, index: number) {
    this.rooms[index] = this.clonedProducts[room.id as string];
    delete this.clonedProducts[room.id as string];
  }

  onRowDelete(room: any, index: number, event: Event) {

    this.confirmationService.confirm({
      target: event.target as EventTarget,
      message: 'Do you want to delete this record?',
      header: 'Danger Zone',
      icon: 'pi pi-info-circle',
      rejectLabel: 'Cancel',
      rejectButtonProps: {
        label: 'Cancel',
        severity: 'secondary',
        outlined: true,
      },
      acceptButtonProps: {
        label: 'Delete',
        severity: 'danger',
      },

      accept: () => {
        this.rooms[index] = this.clonedProducts[room.id as string];
        delete this.clonedProducts[room.id as string];

        this.messageService.add({ severity: 'info', summary: 'Confirmed', detail: 'Record deleted' });

      },
      reject: () => {
      },
    });




  }



}
