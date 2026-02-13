import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PLATFORM_ID } from '@angular/core';

import { HeaderComponent } from './header.component';
import { TranslocoService } from '@jsverse/transloco';

describe('HeaderComponent', () => {
  let component: HeaderComponent;
  let fixture: ComponentFixture<HeaderComponent>;
  let transloco: { setActiveLang: jasmine.Spy; getActiveLang: jasmine.Spy };

  beforeEach(async () => {
    transloco = {
      setActiveLang: jasmine.createSpy('setActiveLang'),
      getActiveLang: jasmine.createSpy('getActiveLang').and.returnValue('en')
    };

    await TestBed.configureTestingModule({
      imports: [HeaderComponent],
      providers: [
        { provide: PLATFORM_ID, useValue: 'browser' },
        { provide: TranslocoService, useValue: transloco }
      ]
    })
      .overrideComponent(HeaderComponent, { set: { template: '' } })
      .compileComponents();

    fixture = TestBed.createComponent(HeaderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    localStorage.removeItem('remote-checkin-lang');
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should set language when supported code is selected', () => {
    component.changeLanguage('it');
    expect(transloco.setActiveLang).toHaveBeenCalledWith('it');
  });
});
