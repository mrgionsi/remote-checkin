import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { SuperadminDashboardComponent } from './superadmin-dashboard.component';
import { SuperadminService } from '../../../services/superadmin.service';

describe('SuperadminDashboardComponent', () => {
  let component: SuperadminDashboardComponent;
  let fixture: ComponentFixture<SuperadminDashboardComponent>;
  let service: jasmine.SpyObj<SuperadminService>;

  beforeEach(async () => {
    service = jasmine.createSpyObj('SuperadminService', ['getDashboardData']);
    service.getDashboardData.and.returnValue(of({
      dashboard: {
        total_structures: 1,
        active_structures: 1,
        archived_structures: 0,
        total_users: 1,
        admin_users: 1,
        superadmin_users: 0,
        unassigned_admins: 0,
        total_reservations: 0
      }
    }));

    await TestBed.configureTestingModule({
      imports: [SuperadminDashboardComponent],
      providers: [{ provide: SuperadminService, useValue: service }]
    })
      .overrideComponent(SuperadminDashboardComponent, { set: { template: '' } })
      .compileComponents();

    fixture = TestBed.createComponent(SuperadminDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should request dashboard data on init', () => {
    expect(service.getDashboardData).toHaveBeenCalled();
    expect(component.loading).toBeFalse();
  });
});
