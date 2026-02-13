import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { SuperadminStructuresComponent } from './structures.component';
import { SuperadminService } from '../../../services/superadmin.service';
import { ErrorHandlerService } from '../../../services/error-handler.service';

describe('SuperadminStructuresComponent', () => {
  let component: SuperadminStructuresComponent;
  let fixture: ComponentFixture<SuperadminStructuresComponent>;
  let service: jasmine.SpyObj<SuperadminService>;

  beforeEach(async () => {
    service = jasmine.createSpyObj('SuperadminService', [
      'getStructures',
      'createStructure',
      'updateStructure',
      'deleteStructure',
      'restoreStructure'
    ]);
    service.getStructures.and.returnValue(of({ structures: [], pagination: { page: 1 } }));

    await TestBed.configureTestingModule({
      imports: [SuperadminStructuresComponent],
      providers: [
        { provide: SuperadminService, useValue: service },
        { provide: ErrorHandlerService, useValue: { getErrorMessageString: () => 'error' } }
      ]
    })
      .overrideComponent(SuperadminStructuresComponent, { set: { template: '' } })
      .compileComponents();

    fixture = TestBed.createComponent(SuperadminStructuresComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load structures on init', () => {
    expect(service.getStructures).toHaveBeenCalled();
    expect(component.loading).toBeFalse();
  });
});
