import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AdminHomeComponent } from './admin-home.component';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { RouterTestingModule } from '@angular/router/testing';

describe('AdminHomeComponent', () => {
  let component: AdminHomeComponent;
  let fixture: ComponentFixture<AdminHomeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        AdminHomeComponent, // Standalone components go in imports, not declarations
        NoopAnimationsModule, // Prevent animation-related errors
        RouterTestingModule // Mocks Angular routing
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(AdminHomeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize menuItems with correct values', () => {
    expect(component.menuItems.length).toBe(4);
    expect(component.menuItems[0].label).toBe('Dashboard');
  });

  it('should toggle sidebar visibility', () => {
    expect(component.visible).toBeFalse();
    component.toggleSidebar();
    expect(component.visible).toBeTrue();
  });
});
