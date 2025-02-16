import { Component, OnInit } from '@angular/core';
import { TableModule } from 'primeng/table';
import { RoomService } from '../../services/room.service';
import { ConfirmationService, MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button'; // Required for buttons in the dialog
import { InputTextModule } from 'primeng/inputtext'; // Required for input fields
import { FormsModule } from '@angular/forms'; // Required for [(ngModel)]
import { CommonModule } from '@angular/common';
import { ToastModule } from 'primeng/toast';
import { TagModule } from 'primeng/tag';
import { SelectModule } from 'primeng/select';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { Dialog } from 'primeng/dialog';


@Component({
  selector: 'app-room',
  imports: [TableModule,
    ButtonModule,
    InputTextModule,
    SelectModule,
    TagModule,
    CommonModule,
    ToastModule,
    ConfirmDialogModule,
    Dialog,
    FormsModule],
  templateUrl: './room.component.html',
  styleUrl: './room.component.scss',
  providers: [MessageService, ConfirmationService]
})
export class RoomComponent implements OnInit {

  clonedProducts: { [s: string]: any } = {};
  add_room_visible: boolean = false;
  new_room: any = { name: '', capacity: '', id_structure: 1 };
  rooms: any;
  editDialogVisible = false;
  selectedRoom: any = {};




  constructor(private messageService: MessageService,
    public confirmationService: ConfirmationService,
    private roomService: RoomService) { }


  ngOnInit(): void {
    this.roomService.getRooms().subscribe({
      next: (value) => {
        console.log(value)
        this.rooms = value
      },
      error: (msg) => {
        console.error("Failed to fetch rooms")
        this.messageService.add({ severity: 'warn', summary: 'Failed', detail: 'Getting rooms. Please try again or contact your administrator.' });

      }
    }
    )
  }
  onRowEditInit(room: any) {
    this.clonedProducts[room.id as string] = { ...room };
  }

  onRowEditSave(room: any) {
    var _ = this;
    this.roomService.editRoom(room).subscribe({
      next: (val) => {
        console.log(val)
        _.messageService.add({ severity: 'info', summary: 'Confirmed', detail: 'Edited Room ' + this.new_room.name + ' added.' });
      },
      error: (error) => {
        console.error('Error editing reservations:', error);
        _.messageService.add({ severity: 'warn', summary: 'Failed', detail: 'Error editing room. Please try again or contact your administrator.' });
      },
    })
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
        var _ = this;
        this.roomService.deleteRoom(room.id).subscribe({
          next: (value) => {
            console.log(value);
            this.rooms[index] = this.clonedProducts[room.id as string];
            delete this.clonedProducts[room.id as string];

            this.messageService.add({ severity: 'info', summary: 'Confirmed', detail: value.message });

          },
          error: (error) => {
            console.error('Error deleting reservations:', error);
            _.messageService.add({ severity: 'warn', summary: 'Failed', detail: 'Error deleting new room. Please try again or contact your administrator.' });
          },
        })

      },
      reject: () => {
      },
    });
  }
  showDialogCreateRoom() {
    this.add_room_visible = true;

  }

  addRoom() {
    this.add_room_visible = false;
    var _ = this;
    this.roomService.addRoom(this.new_room).subscribe({
      next: (val) => {
        _.messageService.add({ severity: 'info', summary: 'Confirmed', detail: 'New Room ' + this.new_room.name + ' added.' });
        _.rooms.push(val);
        _.new_room = { name: '', capacity: '' };
      },
      error: (error) => {
        console.error('Error adding reservations:', error);
        _.messageService.add({ severity: 'warn', summary: 'Failed', detail: 'Error adding new room. Please try again or contact your administrator.' });
      },
    })

  }

}
