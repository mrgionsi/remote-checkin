import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { SuperadminUsersComponent } from './users.component';
import { SuperadminService } from '../../../services/superadmin.service';
import { ErrorHandlerService } from '../../../services/error-handler.service';
import { TranslocoService } from '@jsverse/transloco';

describe('SuperadminUsersComponent', () => {
  let component: SuperadminUsersComponent;
  let fixture: ComponentFixture<SuperadminUsersComponent>;
  let service: jasmine.SpyObj<SuperadminService>;

  beforeEach(async () => {
    service = jasmine.createSpyObj('SuperadminService', [
      'getUsers',
      'getRoles',
      'getStructures',
      'createUser',
      'updateUser',
      'resetUserPassword',
      'createAssociation',
      'deleteAssociation',
      'changeUserRole'
    ]);
    service.getUsers.and.returnValue(of({ users: [], pagination: { page: 1 } }));

    await TestBed.configureTestingModule({
      imports: [SuperadminUsersComponent],
      providers: [
        { provide: SuperadminService, useValue: service },
        { provide: ErrorHandlerService, useValue: { getErrorMessageString: () => 'error' } },
        { provide: TranslocoService, useValue: { translate: (key: string) => key } }
      ]
    })
      .overrideComponent(SuperadminUsersComponent, { set: { template: '' } })
      .compileComponents();

    fixture = TestBed.createComponent(SuperadminUsersComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load users on init', () => {
    expect(service.getUsers).toHaveBeenCalled();
  });
});
