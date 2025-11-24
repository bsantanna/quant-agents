import { TestBed } from '@angular/core/testing';

import { MarketsStatsService } from './markets-stats.service';

describe('MarketsStats', () => {
  let service: MarketsStatsService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(MarketsStatsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
