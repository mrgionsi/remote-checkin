import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UploadIdentityComponent } from './upload-identity.component';

describe('UploadIdentityComponent', () => {
  let component: UploadIdentityComponent;
  let fixture: ComponentFixture<UploadIdentityComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UploadIdentityComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(UploadIdentityComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
