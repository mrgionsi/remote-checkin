import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { JobsMonitorComponent } from './jobs-monitor.component';
import { ActivityService } from '../../services/activity.service';
import { TranslocoService } from '@jsverse/transloco';

describe('JobsMonitorComponent', () => {
  let component: JobsMonitorComponent;
  let fixture: ComponentFixture<JobsMonitorComponent>;
  let activityService: jasmine.SpyObj<ActivityService>;

  beforeEach(async () => {
    activityService = jasmine.createSpyObj('ActivityService', ['getRecentJobs']);
    activityService.getRecentJobs.and.returnValue(of({
      items: [
        {
          id: 10,
          jobType: 'portale.submit',
          status: 'queued',
          attempts: 0,
          maxAttempts: 3,
          errorMessage: null,
          structureId: 1,
          createdByUserId: 2,
          createdAt: '2026-02-23T10:00:00Z',
          availableAt: '2026-02-23T10:00:00Z',
          finishedAt: null
        }
      ],
      pagination: { total: 1, limit: 20, offset: 0 }
    }));

    await TestBed.configureTestingModule({
      imports: [JobsMonitorComponent],
      providers: [
        { provide: ActivityService, useValue: activityService },
        { provide: TranslocoService, useValue: { translate: (key: string) => key } }
      ]
    })
      .overrideComponent(JobsMonitorComponent, { set: { template: '' } })
      .compileComponents();

    fixture = TestBed.createComponent(JobsMonitorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create and load jobs', () => {
    expect(component).toBeTruthy();
    expect(activityService.getRecentJobs).toHaveBeenCalled();
    expect(component.items.length).toBe(1);
    expect(component.total).toBe(1);
  });

  it('should clear filters and reload', () => {
    component.statusFilter = 'failed';
    component.jobTypeFilter = 'portale.submit';

    component.clearFilters();

    expect(component.statusFilter).toBe('');
    expect(component.jobTypeFilter).toBe('');
    expect(activityService.getRecentJobs).toHaveBeenCalled();
  });
});
