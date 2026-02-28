import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ButtonModule } from 'primeng/button';
import { TranslocoPipe, TranslocoService } from '@jsverse/transloco';
import { ActivityItem, ActivityResponse, ActivityService } from '../../services/activity.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-activity-timeline',
  standalone: true,
  imports: [CommonModule, ButtonModule, TranslocoPipe],
  templateUrl: './activity-timeline.component.html',
  styleUrl: './activity-timeline.component.scss'
})
export class ActivityTimelineComponent implements OnInit {
  items: ActivityItem[] = [];
  loading = false;
  page = 1;
  perPage = 20;
  totalPages = 0;
  total = 0;
  private readonly isSuperadmin: boolean;

  constructor(
    private readonly activityService: ActivityService,
    private readonly authService: AuthService,
    private readonly translocoService: TranslocoService
  ) {
    this.isSuperadmin = this.authService.isSuperAdmin();
  }

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    const structureId = this.getStructureIdForAdmin();
    const actorRole = this.isSuperadmin ? undefined : 'administrator,admin,superadmin';
    const actorUserId = this.isSuperadmin ? undefined : Number(this.authService.getUser()?.id || 0);
    const scopedActorUserId =
      actorUserId !== undefined && actorUserId > 0 ? actorUserId : undefined;

    this.activityService
      .getRecentActivity(
        this.perPage,
        structureId,
        actorRole,
        this.page,
        scopedActorUserId
      )
      .subscribe({
        next: (response: ActivityResponse) => {
          this.items = response.items || [];
          this.totalPages = response.pagination?.pages || 0;
          this.total = response.pagination?.total || 0;
          this.loading = false;
        },
        error: () => {
          this.items = [];
          this.totalPages = 0;
          this.total = 0;
          this.loading = false;
        }
      });
  }

  nextPage(): void {
    if (this.page < this.totalPages) {
      this.page += 1;
      this.load();
    }
  }

  prevPage(): void {
    if (this.page > 1) {
      this.page -= 1;
      this.load();
    }
  }

  getTimelineWhen(isoDate: string): string {
    const eventDate = new Date(isoDate);
    if (isNaN(eventDate.getTime())) return '';
    const deltaMinutes = Math.max(0, Math.floor((Date.now() - eventDate.getTime()) / 60000));
    if (deltaMinutes < 1) return this.translocoService.translate('timeline-just-now');
    if (deltaMinutes < 60) return this.translocoService.translate('timeline-minutes-ago', { count: deltaMinutes });
    const deltaHours = Math.floor(deltaMinutes / 60);
    if (deltaHours < 24) return this.translocoService.translate('timeline-hours-ago', { count: deltaHours });
    const deltaDays = Math.floor(deltaHours / 24);
    return this.translocoService.translate('timeline-days-ago', { count: deltaDays });
  }

  getTimelineDescription(item: ActivityItem): string {
    const key = `timeline-event-${item.eventType.replaceAll('.', '-')}`;
    return this.translocoService.translate(key, item.metadata || {});
  }

  getTimelineIcon(eventType: string): string {
    if (eventType.startsWith('reservation.')) return 'pi pi-calendar';
    if (eventType.startsWith('room.')) return 'pi pi-home';
    if (eventType.startsWith('structure.')) return 'pi pi-building';
    if (eventType.startsWith('user.')) return 'pi pi-user';
    if (eventType.startsWith('association.')) return 'pi pi-link';
    return 'pi pi-clock';
  }

  private getStructureIdForAdmin(): number | undefined {
    if (this.isSuperadmin) return undefined;
    const raw = localStorage.getItem('selected_structure_id');
    const parsed = Number(raw || 0);
    return parsed > 0 ? parsed : undefined;
  }
}
