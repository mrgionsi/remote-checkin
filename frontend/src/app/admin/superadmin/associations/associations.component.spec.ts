import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { SuperadminAssociationsComponent } from './associations.component';
import { SuperadminService } from '../../../services/superadmin.service';

describe('SuperadminAssociationsComponent', () => {
  let component: SuperadminAssociationsComponent;
  let fixture: ComponentFixture<SuperadminAssociationsComponent>;
  let service: jasmine.SpyObj<SuperadminService>;

  beforeEach(async () => {
    service = jasmine.createSpyObj('SuperadminService', ['getAssociations', 'getUsers', 'getStructures']);
    service.getAssociations.and.returnValue(of({ associations: [] }));
    service.getUsers.and.returnValue(of({ users: [] }));
    service.getStructures.and.returnValue(of({ structures: [] }));

    await TestBed.configureTestingModule({
      imports: [SuperadminAssociationsComponent],
      providers: [{ provide: SuperadminService, useValue: service }]
    })
      .overrideComponent(SuperadminAssociationsComponent, { set: { template: '' } })
      .compileComponents();

    fixture = TestBed.createComponent(SuperadminAssociationsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load initial datasets on init', () => {
    expect(service.getAssociations).toHaveBeenCalled();
    expect(service.getUsers).toHaveBeenCalled();
    expect(service.getStructures).toHaveBeenCalled();
  });
});
