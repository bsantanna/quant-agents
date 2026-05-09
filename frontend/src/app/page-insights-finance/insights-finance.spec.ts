import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { InsightsFinance } from './insights-finance';
import { FeedbackMessageService } from '../shared';
import { DateFormatService } from '../shared/services/date-format.service';
import { IndexedKeyTickerService } from '../shared/services/indexed-key-ticker.service';
import { MarketsInsightsService } from '../shared/services/markets-insights.service';

describe('InsightsFinance', () => {
  let component: InsightsFinance;
  let fixture: ComponentFixture<InsightsFinance>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsFinance],
      providers: [
        {provide: MarketsInsightsService, useValue: {
          getInsightsNewsList: jest.fn().mockReturnValue(of({items: [], cursor: null})),
          getInsightsNewsItem: jest.fn().mockReturnValue(of({items: [], cursor: null})),
        }},
        {provide: IndexedKeyTickerService, useValue: {indexedKeyTickers: jest.fn().mockReturnValue([])}},
        {provide: DateFormatService, useValue: {format: jest.fn((v: string) => v)}},
        {provide: FeedbackMessageService, useValue: {update: jest.fn()}},
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(InsightsFinance);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('configures the briefings list for the finance index', () => {
    expect(component.indexName).toBe('quaks_insights-finance');
    expect(component.sharePathPrefix).toBe('/insights/financial/item');
  });
});
