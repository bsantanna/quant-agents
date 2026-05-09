import { ComponentFixture, TestBed } from '@angular/core/testing';
import {ActivatedRoute, convertToParamMap, Router} from '@angular/router';
import { of } from 'rxjs';

import { InsightsNewsItem } from './insights-news-item';
import {DateFormatService, SeoService, ShareUrlService} from '../shared';
import {IndexedKeyTickerService} from '../shared/services/indexed-key-ticker.service';
import {MarketsInsightsService} from '../shared/services/markets-insights.service';

describe('InsightsNewsItem', () => {
  let component: InsightsNewsItem;
  let fixture: ComponentFixture<InsightsNewsItem>;
  const insightsService = {
    getInsightsNewsItem: jest.fn(),
  };
  const tickerService = {
    indexedKeyTickers: jest.fn().mockReturnValue([{key_ticker: 'AAPL'}]),
  };
  const shareUrlService = {
    update: jest.fn(),
  };
  const seoService = {
    update: jest.fn(),
    reset: jest.fn(),
  };
  const dateFormatService = {
    format: jest.fn((value: string) => `formatted:${value}`),
  };

  beforeEach(async () => {
    jest.clearAllMocks();
    insightsService.getInsightsNewsItem.mockReturnValue(of({
      items: [{
        id: 'news-1',
        date: '2026-04-09T10:00:00Z',
        executive_summary: 'Insight summary',
        report_html: 'Headline<br>(AAPL)',
        skill_name: '/macro_research',
      }],
      cursor: null,
    }));
    jest.spyOn(window, 'print').mockImplementation(() => undefined);

    await TestBed.configureTestingModule({
      imports: [InsightsNewsItem],
      providers: [
        {provide: ActivatedRoute, useValue: {paramMap: of(convertToParamMap({indexName: 'insights', newsItemId: 'news-1'}))}},
        {provide: Router, useValue: {url: '/insights/news/item/insights/news-1'}},
        {provide: MarketsInsightsService, useValue: insightsService},
        {provide: IndexedKeyTickerService, useValue: tickerService},
        {provide: ShareUrlService, useValue: shareUrlService},
        {provide: SeoService, useValue: seoService},
        {provide: DateFormatService, useValue: dateFormatService},
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(InsightsNewsItem);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('loads the news item and updates metadata', () => {
    expect(insightsService.getInsightsNewsItem).toHaveBeenCalledWith('insights', 'news-1');
    expect(component.loading()).toBe(false);
    expect(component.item()?.report_html).toContain('ticker-link');
    expect(shareUrlService.update).toHaveBeenCalledWith({
      title: 'Insight summary',
      url: 'http://localhost/insights/news/item/insights/news-1',
    });
    expect(seoService.update).toHaveBeenCalledWith({
      title: 'Insight summary',
      path: '/insights/news/item/insights/news-1',
    });
  });

  it('adds and removes print styles', () => {
    component.downloadPdf();
    expect(document.getElementById('quaks-print-style')).toBeTruthy();
    expect(window.print).toHaveBeenCalled();

    window.dispatchEvent(new Event('afterprint'));
    expect(document.getElementById('quaks-print-style')).toBeNull();
  });

  it('formats dates and resets metadata on destroy', () => {
    expect(component.formatDate('2026-04-09T10:00:00Z')).toBe('formatted:2026-04-09');
    component.ngOnDestroy();
    expect(shareUrlService.update).toHaveBeenLastCalledWith({title: '', url: ''});
    expect(seoService.reset).toHaveBeenCalled();
  });
});
