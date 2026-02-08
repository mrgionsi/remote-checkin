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
import { isPlatformBrowser } from '@angular/common';
import { Inject, PLATFORM_ID } from '@angular/core';
import { TranslocoPipe } from '@jsverse/transloco';

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
    FormsModule, TranslocoPipe],
  templateUrl: './room.component.html',
  styleUrl: './room.component.scss',
  providers: [MessageService, ConfirmationService]
})
export class RoomComponent implements OnInit {

  clonedProducts: { [s: string]: any } = {};
  add_room_visible: boolean = false;
  new_room: any = { name: '', capacity: '', id_structure: 1, is_active: true };
  rooms: any[] = [];
  filteredRooms: any[] = [];
  searchTerm: string = '';
  capacityFilter: string = 'all';
  statusFilter: string = 'all';
  capacityOptions = [
    { label: 'All capacities', value: 'all' },
    { label: '1-2 guests', value: '1-2' },
    { label: '3-4 guests', value: '3-4' },
    { label: '5-6 guests', value: '5-6' },
    { label: '7+ guests', value: '7+' }
  ];
  statusOptions = [
    { label: 'All statuses', value: 'all' },
    { label: 'Active', value: 'active' },
    { label: 'Inactive', value: 'inactive' }
  ];
  editDialogVisible = false;
  selectedRoom: any = {};




  constructor(private messageService: MessageService,
    public confirmationService: ConfirmationService,
    private roomService: RoomService,
    @Inject(PLATFORM_ID) private platformId: object) { }


  ngOnInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      this.roomService.getRooms().subscribe({
        next: (value) => {
          console.log(value)
          this.rooms = (value || []).map((room: any) => ({
            ...room,
            isActive: room.is_active ?? room.isActive ?? true
          }));
          this.applyFilters();
        },
        error: (msg) => {
          console.error("Failed to fetch rooms")
          this.messageService.add({ severity: 'warn', summary: 'Failed', detail: 'Getting rooms. Please try again or contact your administrator.' });

        }
      })
    }
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
    const originalIndex = this.rooms.findIndex((item) => item.id === room.id);
    if (originalIndex !== -1) {
      this.rooms[originalIndex] = this.clonedProducts[room.id as string];
    }
    delete this.clonedProducts[room.id as string];
    this.applyFilters();
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
            const originalIndex = this.rooms.findIndex((item) => item.id === room.id);
            if (originalIndex !== -1) {
              this.rooms.splice(originalIndex, 1);
            }
            this.applyFilters();

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
        _.rooms.push({ ...val, isActive: val?.is_active ?? true });
        _.applyFilters();
        _.new_room = { name: '', capacity: '', id_structure: 1, is_active: true };
      },
      error: (error) => {
        console.error('Error adding reservations:', error);
        _.messageService.add({ severity: 'warn', summary: 'Failed', detail: 'Error adding new room. Please try again or contact your administrator.' });
      },
    })

  }

  onSearchChange(event: Event) {
    const target = event.target as HTMLInputElement;
    this.searchTerm = target.value;
    this.applyFilters();
  }

  onCapacityChange(event: any) {
    this.capacityFilter = event.value;
    this.applyFilters();
  }

  onStatusChange(event: any) {
    this.statusFilter = event.value;
    this.applyFilters();
  }

  toggleRoomStatus(room: any) {
    room.isActive = !room.isActive;
    room.is_active = room.isActive;
    this.roomService.editRoom(room).subscribe({
      next: () => {
        this.applyFilters();
      },
      error: () => {
        room.isActive = !room.isActive;
        room.is_active = room.isActive;
        this.messageService.add({
          severity: 'warn',
          summary: 'Failed',
          detail: 'Could not update room status. Please try again.'
        });
      }
    });
  }

  private applyFilters() {
    const term = this.searchTerm.trim().toLowerCase();
    this.filteredRooms = (this.rooms || []).filter((room) => {
      const matchesSearch =
        !term ||
        String(room.id).toLowerCase().includes(term) ||
        String(room.name || '').toLowerCase().includes(term);

      const capacity = Number(room.capacity || 0);
      let matchesCapacity = true;
      switch (this.capacityFilter) {
        case '1-2':
          matchesCapacity = capacity >= 1 && capacity <= 2;
          break;
        case '3-4':
          matchesCapacity = capacity >= 3 && capacity <= 4;
          break;
        case '5-6':
          matchesCapacity = capacity >= 5 && capacity <= 6;
          break;
        case '7+':
          matchesCapacity = capacity >= 7;
          break;
        default:
          matchesCapacity = true;
      }

      let matchesStatus = true;
      if (this.statusFilter === 'active') {
        matchesStatus = !!room.isActive;
      } else if (this.statusFilter === 'inactive') {
        matchesStatus = !room.isActive;
      }

      return matchesSearch && matchesCapacity && matchesStatus;
    });
  }

}
