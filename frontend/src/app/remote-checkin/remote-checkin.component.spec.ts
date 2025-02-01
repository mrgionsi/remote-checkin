import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RemoteCheckinComponent } from './remote-checkin.component';

describe('RemoteCheckinComponent', () => {
  let component: RemoteCheckinComponent;
  let fixture: ComponentFixture<RemoteCheckinComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RemoteCheckinComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(RemoteCheckinComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
