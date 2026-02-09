import { ComponentFixture, fakeAsync, TestBed, tick } from '@angular/core/testing';
import { RoomComponent } from './room.component';
import { RoomService } from '../../services/room.service';
import { ConfirmationService, MessageService } from 'primeng/api';
import { of, throwError } from 'rxjs';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ToastModule } from 'primeng/toast';
import { SelectModule } from 'primeng/select';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DialogModule } from 'primeng/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslocoService } from '@jsverse/transloco';
import { AuthService } from '../../services/auth.service';

describe('RoomComponent', () => {
  let component: RoomComponent;
  let fixture: ComponentFixture<RoomComponent>;
  let mockRoomService: jasmine.SpyObj<RoomService>;

  beforeEach(async () => {
    mockRoomService = jasmine.createSpyObj('RoomService', ['getRooms', 'editRoom', 'deleteRoom', 'addRoom']);

    await TestBed.configureTestingModule({
      imports: [
        RoomComponent,
        TableModule,
        ButtonModule,
        InputTextModule,
        SelectModule,
        CommonModule,
        ToastModule,
        ConfirmDialogModule,
        DialogModule,
        FormsModule,
        NoopAnimationsModule
      ],
      providers: [
        { provide: RoomService, useValue: mockRoomService },
        { provide: AuthService, useValue: { getUser: () => ({ structures: [] }) } },
        { provide: TranslocoService, useValue: { translate: (key: string) => key } },
        MessageService,
        ConfirmationService
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(RoomComponent);
    component = fixture.componentInstance;

    // ✅ Ensure `getRooms` is always returning an observable
    mockRoomService.getRooms.and.returnValue(of([]));

    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should fetch rooms on initialization', () => {
    const mockRooms = [{ id: 1, name: 'Deluxe', capacity: 2 }];
    mockRoomService.getRooms.and.returnValue(of(mockRooms));

    component.ngOnInit(); // Manually trigger ngOnInit
    fixture.detectChanges();

    expect(mockRoomService.getRooms).toHaveBeenCalled();
    expect(component.rooms[0].name).toEqual('Deluxe');
  });

  it('should handle error when fetching rooms', () => {
    const messageService = TestBed.inject(MessageService);
    spyOn(messageService, 'add');
    mockRoomService.getRooms.and.returnValue(throwError(() => new Error('Failed to fetch rooms')));

    component.ngOnInit();
    fixture.detectChanges();

    expect(messageService.add).toHaveBeenCalled();
  });

  it('should edit a room successfully', fakeAsync(() => {
    const mockRoom = { id: 1, name: 'Deluxe', capacity: 2 };
    mockRoomService.editRoom.and.returnValue(of(mockRoom));

    component.onRowEditSave(mockRoom);
    tick(); // Simulate async passage of time

    expect(mockRoomService.editRoom).toHaveBeenCalledWith(mockRoom);
  }));

  it('should handle error when editing a room', fakeAsync(() => {
    const messageService = TestBed.inject(MessageService);
    spyOn(messageService, 'add');
    const mockRoom = { id: 1, name: 'Deluxe', capacity: 2 };
    mockRoomService.editRoom.and.returnValue(throwError(() => new Error('Failed to edit room')));

    component.onRowEditSave(mockRoom);
    tick();

    expect(messageService.add).toHaveBeenCalled();
  }));

  it('should delete a room successfully', fakeAsync(() => {
    const mockRoom = { id: 1, name: 'Deluxe', capacity: 2 };
    const mockEvent = new Event('click');
    mockRoomService.deleteRoom.and.returnValue(of({ message: 'Room deleted successfully' }));

    // Mock confirmation dialog behavior
    spyOn(component.confirmationService, 'confirm').and.callFake((confirmation) => {
      // Directly calling accept to simulate user confirming the deletion
      return confirmation.accept!();
    });

    component.onRowDelete(mockRoom, 0, mockEvent);
    tick(); // Simulate async passage of time

    expect(mockRoomService.deleteRoom).toHaveBeenCalledWith(mockRoom.id);
  }));


  it('should handle error when deleting a room', fakeAsync(() => {
    spyOn(console, 'error');
    const mockRoom = { id: 1, name: 'Deluxe', capacity: 2 };
    const mockEvent = new Event('click');
    mockRoomService.deleteRoom.and.returnValue(throwError(() => new Error('Failed to delete room')));

    spyOn(component.confirmationService, 'confirm').and.callFake((confirmation) => confirmation.accept!());

    component.onRowDelete(mockRoom, 0, mockEvent);
    tick();

    expect(mockRoomService.deleteRoom).toHaveBeenCalledWith(mockRoom.id);

    expect(console.error).toHaveBeenCalledWith('Error deleting reservations:', jasmine.any(Error));
  }));

  it('should add a room successfully', fakeAsync(() => {
    const newRoom = { name: 'Suite', capacity: 3 };
    mockRoomService.addRoom.and.returnValue(of(newRoom));

    component.new_room = newRoom;
    component.addRoom();
    tick();

    expect(mockRoomService.addRoom).toHaveBeenCalledWith(newRoom);
  }));

  it('should handle error when adding a room', fakeAsync(() => {
    spyOn(console, 'error');
    const newRoom = { name: 'Suite', capacity: 3 };
    mockRoomService.addRoom.and.returnValue(throwError(() => new Error('Failed to add room')));

    component.new_room = newRoom;
    component.addRoom();
    tick();

    expect(console.error).toHaveBeenCalledWith('Error adding reservations:', jasmine.any(Error));
  }));
});
