import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { environment } from '../../environments/environments';

export const jobsFeatureGuard: CanActivateFn = (): boolean => {
  const router = inject(Router);
  if (environment.enableJobsMonitor) {
    return true;
  }
  router.navigate(['/admin/dashboard']);
  return false;
};
