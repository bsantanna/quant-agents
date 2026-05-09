import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { BriefingsList } from './briefings-list';
import { FeedbackMessageService } from '../../services/feedback-message.service';
import { DateFormatService } from '../../services/date-format.service';
import { IndexedKeyTickerService } from '../../services/indexed-key-ticker.service';
import { MarketsInsightsService } from '../../services/markets-insights.service';

describe('BriefingsList', () => {
  let component: BriefingsList;
  let fixture: ComponentFixture<BriefingsList>;
  const insightsService = {
    getInsightsNewsList: jest.fn(),
    getInsightsNewsItem: jest.fn(),
  };
  const tickerService = {
    indexedKeyTickers: jest.fn().mockReturnValue([{key_ticker: 'AAPL'}]),
  };
  const dateFormatService = {
    format: jest.fn((value: string) => `formatted:${value}`),
  };
  const feedbackMessageService = {
    update: jest.fn(),
  };
  const initialItem = {
    id: 'item-1',
    date: '2026-04-09T09:15:00Z',
    executive_summary: 'Summary',
    report_html: null,
    skill_name: '/macro_research',
    author_username: 'analyst',
  };

  beforeEach(async () => {
    jest.clearAllMocks();
    insightsService.getInsightsNewsList.mockReturnValue(of({
      items: [initialItem],
      cursor: 'cursor-1',
    }));
    insightsService.getInsightsNewsItem.mockReturnValue(of({
      items: [{...initialItem, report_html: 'Headline<br>(AAPL)'}],
      cursor: null,
    }));
    Object.defineProperty(navigator, 'clipboard', {
      value: {writeText: jest.fn()},
      configurable: true,
    });

    await TestBed.configureTestingModule({
      imports: [BriefingsList],
      providers: [
        {provide: MarketsInsightsService, useValue: insightsService},
        {provide: IndexedKeyTickerService, useValue: tickerService},
        {provide: DateFormatService, useValue: dateFormatService},
        {provide: FeedbackMessageService, useValue: feedbackMessageService},
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(BriefingsList);
    fixture.componentRef.setInput('indexName', 'quaks_insights-news');
    fixture.componentRef.setInput('sharePathPrefix', '/insights/news/item');
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('loads the first page on construction', () => {
    expect(insightsService.getInsightsNewsList).toHaveBeenCalledWith('quaks_insights-news', 10, '');
    expect(component.items()).toHaveLength(1);
    expect(component.cursor()).toBe('cursor-1');
    expect(component.hasMore()).toBe(true);
  });

  it('loads more items when a cursor is available', () => {
    component.loadMore();
    expect(insightsService.getInsightsNewsList).toHaveBeenCalledWith('quaks_insights-news', 10, 'cursor-1');
  });

  it('does not load more when already loading or out of pages', () => {
    component.loading.set(true);
    component.loadMore();
    expect(insightsService.getInsightsNewsList).toHaveBeenCalledTimes(1);

    component.loading.set(false);
    component.cursor.set(null);
    component.loadMore();
    expect(insightsService.getInsightsNewsList).toHaveBeenCalledTimes(1);
  });

  it('toggles reports and sanitizes fetched report html', () => {
    component.toggleReport({...initialItem, report_html: '<p>ready</p>'});
    expect(component.expandedId()).toBe('item-1');

    component.toggleReport({...initialItem, report_html: '<p>ready</p>'});
    expect(component.expandedId()).toBeNull();

    component.toggleReport(initialItem);
    expect(insightsService.getInsightsNewsItem).toHaveBeenCalledWith('quaks_insights-news', 'item-1');
    expect(component.expandedId()).toBe('item-1');
    expect(component.items()[0].report_html).toContain('ticker-link');
  });

  it('toggles the share menu and handles share actions', () => {
    const openSpy = jest.spyOn(window, 'open').mockImplementation(() => null);

    component.toggleShare('item-1');
    expect(component.shareOpenId()).toBe('item-1');

    component.toggleShare('item-1');
    expect(component.shareOpenId()).toBeNull();

    component.share('copy', initialItem);
    expect(component.shareOpenId()).toBeNull();
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('http://localhost/insights/news/item/quaks_insights-news/item-1');
    expect(feedbackMessageService.update).toHaveBeenCalled();

    component.share('facebook', initialItem);
    expect(openSpy).toHaveBeenCalledWith(
      'https://www.facebook.com/sharer.php?u=http%3A%2F%2Flocalhost%2Finsights%2Fnews%2Fitem%2Fquaks_insights-news%2Fitem-1',
      '_blank',
    );
  });

  it('uses sharePathPrefix when building share URLs', () => {
    fixture.componentRef.setInput('sharePathPrefix', '/insights/financial/item');
    fixture.componentRef.setInput('indexName', 'quaks_insights-finance');
    fixture.detectChanges();

    expect(component.getShareUrl(initialItem))
      .toBe('http://localhost/insights/financial/item/quaks_insights-finance/item-1');
  });

  it('closes the share menu on outside clicks only', () => {
    component.shareOpenId.set('item-1');
    component.onDocumentClick({target: document.createElement('div')} as Event);
    expect(component.shareOpenId()).toBeNull();

    component.shareOpenId.set('item-1');
    const inside = document.createElement('button');
    const host = document.createElement('div');
    host.className = 'briefing-share';
    host.appendChild(inside);
    component.onDocumentClick({target: inside} as Event);
    expect(component.shareOpenId()).toBe('item-1');
  });

  it('formats dates, times, and avatar sources', () => {
    expect(component.agentAvatarSrc('/macro_research')).toBe('/svg/insights-agent_quaks-macro-research.svg');
    expect(component.formatDate('2026-04-09T09:15:00Z')).toBe('formatted:2026-04-09');
    expect(component.formatDate('')).toBe('--');
    expect(component.formatTime('2026-04-09T09:15:00Z')).toMatch(/\d{2}:\d{2}/);
    expect(component.formatTime('')).toBe('');
  });
});
