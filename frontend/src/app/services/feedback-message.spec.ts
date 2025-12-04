import { TestBed } from '@angular/core/testing';

import { FeedbackMessageService } from './feedback-message.service';

describe('FeedbackMessage', () => {
  let service: FeedbackMessageService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(FeedbackMessageService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
