import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FAQComponent } from './faq.component';

describe('FAQComponent', () => {
  let component: FAQComponent;
  let fixture: ComponentFixture<FAQComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FAQComponent]
    })
      .overrideComponent(FAQComponent, { set: { template: '' } })
      .compileComponents();

    fixture = TestBed.createComponent(FAQComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should toggle FAQ item expansion', () => {
    expect(component.categories[0].items[0].expanded).toBeFalse();
    component.toggleItem(0, 0);
    expect(component.categories[0].items[0].expanded).toBeTrue();
  });
});
