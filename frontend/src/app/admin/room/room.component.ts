import { Component, OnInit, Inject, PLATFORM_ID } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DialogModule } from 'primeng/dialog';
import { ConfirmationService, MessageService } from 'primeng/api';
import { TranslocoPipe, TranslocoService } from '@jsverse/transloco';
import { from, of } from 'rxjs';
import { catchError, concatMap, finalize } from 'rxjs/operators';
import { RoomService } from '../../services/room.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-room',
  imports: [
    TableModule,
    ButtonModule,
    InputTextModule,
    SelectModule,
    TagModule,
    CommonModule,
    ToastModule,
    ConfirmDialogModule,
    DialogModule,
    FormsModule,
    TranslocoPipe
  ],
  templateUrl: './room.component.html',
  styleUrl: './room.component.scss',
  providers: [MessageService, ConfirmationService]
})
export class RoomComponent implements OnInit {
  clonedProducts: { [s: string]: any } = {};
  add_room_visible: boolean = false;
  new_room: any = { name: '', capacity: '', id_structure: null, is_active: true };
  structures: { id: number; name: string }[] = [];
  canCreateRoom: boolean = false;

  rooms: any[] = [];
  filteredRooms: any[] = [];
  searchTerm: string = '';
  capacityFilter: string = 'all';
  statusFilter: string = 'all';
  currentStructureId: number | null = null;
  capacityOptions: { label: string; value: string }[] = [];
  statusOptions: { label: string; value: string }[] = [];

  importing: boolean = false;

  constructor(
    private messageService: MessageService,
    public confirmationService: ConfirmationService,
    private roomService: RoomService,
    private authService: AuthService,
    private readonly translocoService: TranslocoService,
    @Inject(PLATFORM_ID) private platformId: object
  ) { }

  ngOnInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      this.setFilterOptions();
      const user = this.authService.getUser();
      this.structures = user?.structures || [];
      const selectedStructureId = Number(localStorage.getItem('selected_structure_id') || 0);
      if (selectedStructureId && this.structures.some((s) => s.id === selectedStructureId)) {
        this.currentStructureId = selectedStructureId;
      } else if (this.structures.length > 0) {
        this.currentStructureId = this.structures[0].id;
      } else {
        this.currentStructureId = null;
      }
      this.new_room.id_structure = this.currentStructureId;
      this.canCreateRoom = !!this.currentStructureId;

      this.roomService.getRooms(this.currentStructureId).subscribe({
        next: (value) => {
          this.rooms = (value || []).map((room: any) => ({
            ...room,
            isActive: room.is_active ?? room.isActive ?? true
          }));
          this.setFilterOptions();
          this.applyFilters();
        },
        error: () => {
          this.messageService.add({
            severity: 'warn',
            summary: 'Failed',
            detail: 'Getting rooms. Please try again or contact your administrator.'
          });
        }
      });
    }
  }

  onRowEditInit(room: any) {
    this.clonedProducts[room.id as string] = { ...room };
  }

  onRowEditSave(room: any) {
    this.roomService.editRoom(room).subscribe({
      next: () => {
        this.messageService.add({ severity: 'info', summary: 'Confirmed', detail: 'Room updated.' });
        this.applyFilters();
      },
      error: () => {
        this.messageService.add({ severity: 'warn', summary: 'Failed', detail: 'Error editing room. Please try again.' });
      }
    });
  }

  onRowEditCancel(room: any) {
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
        this.roomService.deleteRoom(room.id).subscribe({
          next: (value) => {
            const originalIndex = this.rooms.findIndex((item) => item.id === room.id);
            if (originalIndex !== -1) {
              this.rooms.splice(originalIndex, 1);
            }
            this.applyFilters();
            this.messageService.add({ severity: 'info', summary: 'Confirmed', detail: value.message });
          },
          error: () => {
            this.messageService.add({ severity: 'warn', summary: 'Failed', detail: 'Error deleting room.' });
          }
        });
      }
    });
  }

  showDialogCreateRoom() {
    if (!this.canCreateRoom) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Missing structure',
        detail: 'Select a structure before creating a room.'
      });
      return;
    }
    this.add_room_visible = true;
  }

  addRoom() {
    if (!this.new_room.id_structure) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Missing structure',
        detail: 'Select a structure before creating a room.'
      });
      return;
    }
    this.add_room_visible = false;
    this.roomService.addRoom(this.new_room).subscribe({
      next: (val) => {
        this.messageService.add({ severity: 'info', summary: 'Confirmed', detail: 'New room added.' });
        this.rooms.push({ ...val, isActive: val?.is_active ?? true });
        this.applyFilters();
        this.new_room = {
          name: '',
          capacity: '',
          id_structure: this.currentStructureId,
          is_active: true
        };
      },
      error: () => {
        this.messageService.add({ severity: 'warn', summary: 'Failed', detail: 'Error adding new room.' });
      }
    });
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
      next: () => this.applyFilters(),
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

  onCsvImport(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files || !input.files.length || this.importing) {
      return;
    }
    const file = input.files[0];
    this.importing = true;
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result || '');
      const rows = this.parseCsv(text);
      if (!rows.length) {
        this.importing = false;
        this.messageService.add({ severity: 'warn', summary: 'No rows', detail: 'No valid rooms found in CSV.' });
        input.value = '';
        return;
      }
      from(rows)
        .pipe(
          concatMap((row) => this.roomService.addRoom({
            ...row,
            id_structure: this.currentStructureId,
            is_active: row.is_active ?? true
          }).pipe(
            catchError(() => {
              this.messageService.add({
                severity: 'warn',
                summary: 'Skipped',
                detail: `Failed to import room ${row.name}.`
              });
              return of(null);
            })
          )),
          finalize(() => {
            this.importing = false;
            input.value = '';
          })
        )
        .subscribe((val: any) => {
          if (val) {
            this.rooms.push({ ...val, isActive: val?.is_active ?? true });
            this.applyFilters();
          }
        });
    };
    reader.onerror = () => {
      this.importing = false;
      this.messageService.add({ severity: 'warn', summary: 'Failed', detail: 'Could not read CSV file.' });
    };
    reader.readAsText(file);
  }

  private parseCsv(text: string): Array<{ name: string; capacity: number; is_active?: boolean }> {
    const lines = text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
    if (!lines.length) return [];

    let startIndex = 0;
    const header = lines[0].toLowerCase();
    if (header.includes('name') && header.includes('capacity')) {
      startIndex = 1;
    }

    const rows: Array<{ name: string; capacity: number; is_active?: boolean }> = [];
    for (let i = startIndex; i < lines.length; i += 1) {
      const parts = lines[i].split(',').map((part) => part.trim());
      if (parts.length < 2) continue;
      const name = parts[0];
      const capacity = Number(parts[1]);
      if (!name || Number.isNaN(capacity)) continue;
      const isActive = parts[2] ? parts[2].toLowerCase() !== 'false' : true;
      rows.push({ name, capacity, is_active: isActive });
    }
    return rows;
  }

  private setFilterOptions() {
    this.capacityOptions = [
      { label: this.translocoService.translate('rooms-all-capacities'), value: 'all' },
      { label: this.translocoService.translate('rooms-capacity-1-2'), value: '1-2' },
      { label: this.translocoService.translate('rooms-capacity-3-4'), value: '3-4' },
      { label: this.translocoService.translate('rooms-capacity-5-6'), value: '5-6' },
      { label: this.translocoService.translate('rooms-capacity-7-plus'), value: '7+' }
    ];
    this.statusOptions = [
      { label: this.translocoService.translate('rooms-all-statuses'), value: 'all' },
      { label: this.translocoService.translate('rooms-active-label'), value: 'active' },
      { label: this.translocoService.translate('rooms-inactive-label'), value: 'inactive' }
    ];
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
