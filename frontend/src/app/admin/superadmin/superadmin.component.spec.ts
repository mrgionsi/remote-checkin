import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BehaviorSubject } from 'rxjs';
import { provideRouter } from '@angular/router';

import { SuperadminComponent } from './superadmin.component';
import { AuthService } from '../../services/auth.service';

describe('SuperadminComponent', () => {
  let component: SuperadminComponent;
  let fixture: ComponentFixture<SuperadminComponent>;
  const user$ = new BehaviorSubject<any>({ id: 1, role: 'superadmin' });
  const authServiceStub = {
    user$,
    isLoggedIn: () => true,
    isSuperAdmin: () => true
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SuperadminComponent],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: authServiceStub }
      ]
    })
      .overrideComponent(SuperadminComponent, { set: { template: '' } })
      .compileComponents();

    fixture = TestBed.createComponent(SuperadminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
