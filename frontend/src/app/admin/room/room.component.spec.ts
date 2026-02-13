import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { RoomComponent } from './room.component';
import { RoomService } from '../../services/room.service';
import { AuthService } from '../../services/auth.service';
import { TranslocoService } from '@jsverse/transloco';

describe('RoomComponent', () => {
  let component: RoomComponent;
  let fixture: ComponentFixture<RoomComponent>;
  let roomService: jasmine.SpyObj<RoomService>;

  beforeEach(async () => {
    roomService = jasmine.createSpyObj('RoomService', ['getRooms', 'editRoom', 'deleteRoom', 'addRoom']);
    roomService.getRooms.and.returnValue(of([{ id: 1, name: 'Room A', capacity: 2, is_active: true }]));
    roomService.editRoom.and.returnValue(of({}));
    roomService.addRoom.and.returnValue(of({ id: 2, name: 'Room B', capacity: 3, is_active: true }));
    roomService.deleteRoom.and.returnValue(of({}));

    await TestBed.configureTestingModule({
      imports: [RoomComponent],
      providers: [
        { provide: RoomService, useValue: roomService },
        {
          provide: AuthService,
          useValue: {
            getUser: () => ({ structures: [{ id: 1, name: 'Main' }] })
          }
        },
        { provide: TranslocoService, useValue: { translate: (key: string) => key } }
      ]
    })
      .overrideComponent(RoomComponent, { set: { template: '' } })
      .compileComponents();

    localStorage.setItem('selected_structure_id', '1');
    fixture = TestBed.createComponent(RoomComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load rooms and initialize filtered list', () => {
    expect(roomService.getRooms).toHaveBeenCalledWith(1);
    expect(component.rooms.length).toBe(1);
    expect(component.filteredRooms.length).toBe(1);
    expect(component.filteredRooms[0].name).toBe('Room A');
  });

  it('should filter rooms by search term', () => {
    component.rooms = [
      { id: 1, name: 'Blue', capacity: 2, isActive: true },
      { id: 2, name: 'Red', capacity: 4, isActive: true }
    ];
    component.searchTerm = 'red';

    (component as any).applyFilters();

    expect(component.filteredRooms.length).toBe(1);
    expect(component.filteredRooms[0].name).toBe('Red');
  });

  it('should toggle room status and persist success', () => {
    const room = { id: 1, name: 'Blue', capacity: 2, isActive: true, is_active: true };
    roomService.editRoom.and.returnValue(of({}));

    component.toggleRoomStatus(room);

    expect(roomService.editRoom).toHaveBeenCalled();
    expect(room.isActive).toBeFalse();
    expect(room.is_active).toBeFalse();
  });

  it('should rollback status toggle on API error', () => {
    const room = { id: 1, name: 'Blue', capacity: 2, isActive: true, is_active: true };
    roomService.editRoom.and.returnValue(throwError(() => new Error('boom')));
    const addSpy = spyOn((component as any).messageService, 'add');

    component.toggleRoomStatus(room);

    expect(room.isActive).toBeTrue();
    expect(room.is_active).toBeTrue();
    expect(addSpy).toHaveBeenCalled();
  });

  it('should create room and append it to list', () => {
    component.new_room = { name: 'Suite', capacity: 3, id_structure: 1, is_active: true };
    component.addRoom();

    expect(roomService.addRoom).toHaveBeenCalled();
    expect(component.rooms.some((r) => r.name === 'Room B')).toBeTrue();
  });

  it('should delete room when confirmation is accepted', () => {
    component.rooms = [{ id: 1, name: 'Room A', capacity: 2, isActive: true }];
    spyOn(component.confirmationService, 'confirm').and.callFake((cfg: any) => cfg.accept());

    component.onRowDelete(component.rooms[0], 0, new Event('click'));

    expect(roomService.deleteRoom).toHaveBeenCalledWith(1);
    expect(component.rooms.length).toBe(0);
  });
});
