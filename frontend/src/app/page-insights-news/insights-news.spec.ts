import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { InsightsNews } from './insights-news';
import { FeedbackMessageService } from '../shared';
import { DateFormatService } from '../shared/services/date-format.service';
import { IndexedKeyTickerService } from '../shared/services/indexed-key-ticker.service';
import { MarketsInsightsService } from '../shared/services/markets-insights.service';

describe('InsightsNews', () => {
  let component: InsightsNews;
  let fixture: ComponentFixture<InsightsNews>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsNews],
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

    fixture = TestBed.createComponent(InsightsNews);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('configures the briefings list for the news index', () => {
    expect(component.indexName).toBe('quaks_insights-news');
    expect(component.sharePathPrefix).toBe('/insights/news/item');
  });
});
