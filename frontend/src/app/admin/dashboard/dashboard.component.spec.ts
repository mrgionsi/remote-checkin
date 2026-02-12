import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { DashboardComponent } from './dashboard.component';
import { ReservationService } from '../../services/reservation.service';
import { AuthService } from '../../services/auth.service';
import { MessageService } from 'primeng/api';
import { TranslocoService } from '@jsverse/transloco';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let messageService: jasmine.SpyObj<MessageService>;

  const reservationServiceStub = jasmine.createSpyObj('ReservationService', [
    'getReservationByStructureId',
    'getMonthlyReservation'
  ]);
  const authServiceStub = {
    getUser: () => ({ structures: [{ id: 1, name: 'Main' }] })
  };
  const translocoStub = {
    translate: (key: string) => key,
    selectTranslateObject: () => of([])
  };

  beforeEach(async () => {
    reservationServiceStub.getReservationByStructureId.and.returnValue(of([]));
    reservationServiceStub.getMonthlyReservation.and.returnValue(of([]));
    messageService = jasmine.createSpyObj('MessageService', ['add']);

    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [
        { provide: ReservationService, useValue: reservationServiceStub },
        { provide: AuthService, useValue: authServiceStub },
        { provide: MessageService, useValue: messageService },
        { provide: TranslocoService, useValue: translocoStub }
      ]
    })
      .overrideComponent(DashboardComponent, { set: { template: '' } })
      .compileComponents();

    localStorage.setItem('selected_structure_id', '1');
    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should apply status and room filters and keep only matching rows', () => {
    component.reservations = [
      { id_reference: 'A-1', name_reference: 'Mario', room_name: 'Room A', status: 'Pending', start_date: '2026-01-03' },
      { id_reference: 'B-1', name_reference: 'Luigi', room_name: 'Room B', status: 'Approved', start_date: '2026-01-04' }
    ];

    component.statusFilter = 'Pending';
    component.roomFilter = 'Room A';
    component.applyFilters();

    expect(component.filteredReservations.length).toBe(1);
    expect(component.filteredReservations[0].id_reference).toBe('A-1');
  });

  it('should apply global search case-insensitively', () => {
    component.reservations = [
      { id_reference: 'RES-001', name_reference: 'John Doe', room_name: 'Blue', status: 'Pending', start_date: '2026-01-03' },
      { id_reference: 'RES-002', name_reference: 'Jane Doe', room_name: 'Red', status: 'Approved', start_date: '2026-01-04' }
    ];

    component.globalSearchTerm = 'jane';
    component.applyFilters();

    expect(component.filteredReservations.length).toBe(1);
    expect(component.filteredReservations[0].id_reference).toBe('RES-002');
  });

  it('should update recent reservations from active filter source only', () => {
    component.reservations = [
      { id_reference: 'RES-001', name_reference: 'A', room_name: 'X', status: 'Pending', start_date: '2026-01-01' },
      { id_reference: 'RES-002', name_reference: 'B', room_name: 'Y', status: 'Approved', start_date: '2026-01-10' },
      { id_reference: 'RES-003', name_reference: 'C', room_name: 'Y', status: 'Pending', start_date: '2026-01-12' }
    ];

    component.statusFilter = 'Pending';
    component.applyFilters();

    expect(component.filteredReservations.length).toBe(2);
    expect(component.recentReservations.length).toBe(2);
    expect(component.recentReservations[0].id_reference).toBe('RES-003');
    expect(component.recentReservations[1].id_reference).toBe('RES-001');
  });

  it('should clear all filters', () => {
    component.statusFilter = 'Pending';
    component.dateRangeFilter = 'week';
    component.roomFilter = 'Room A';
    component.globalSearchTerm = 'foo';

    component.clearFilters();

    expect(component.statusFilter).toBe('');
    expect(component.dateRangeFilter).toBe('');
    expect(component.roomFilter).toBe('');
    expect(component.globalSearchTerm).toBe('');
  });
});
