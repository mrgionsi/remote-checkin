import { TestBed } from '@angular/core/testing';

import { ClientReservationService } from './client-reservation.service';

describe('ClientReservationService', () => {
  let service: ClientReservationService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ClientReservationService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
