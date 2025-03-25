import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PersonDetailDialogComponent } from './person-detail-dialog.component';

describe('PersonDetailDialogComponent', () => {
  let component: PersonDetailDialogComponent;
  let fixture: ComponentFixture<PersonDetailDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PersonDetailDialogComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PersonDetailDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
