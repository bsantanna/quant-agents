import { TestBed } from '@angular/core/testing';

import { ShareUrlService } from './share-url.service';

describe('ShareUrlService', () => {
  let service: ShareUrlService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ShareUrlService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
