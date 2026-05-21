import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router } from '@angular/router';
import { BehaviorSubject } from 'rxjs';

import { MarketsPerformanceComparison } from './markets-performance-comparison';
import { ShareUrlService } from '../shared';

describe('MarketsPerformanceComparison', () => {
  let component: MarketsPerformanceComparison;
  let fixture: ComponentFixture<MarketsPerformanceComparison>;
  let queryParams$: BehaviorSubject<any>;
  let mockRouter: { navigate: jest.Mock };
  let mockShareUrlService: { update: jest.Mock; getPastDateInDays: jest.Mock; state: any };

  beforeEach(async () => {
    queryParams$ = new BehaviorSubject({});
    mockRouter = { navigate: jest.fn().mockResolvedValue(true) };
    mockShareUrlService = {
      update: jest.fn(),
      getPastDateInDays: jest.fn((days: number) => '2025-01-01'),
      state: { url: '', title: '' },
    };

    await TestBed.configureTestingModule({
      imports: [MarketsPerformanceComparison],
      providers: [
        { provide: ActivatedRoute, useValue: { queryParams: queryParams$.asObservable(), snapshot: { title: 'Performance' } } },
        { provide: Router, useValue: mockRouter },
        { provide: ShareUrlService, useValue: mockShareUrlService },
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MarketsPerformanceComparison);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should parse symbols from query param', () => {
    queryParams$.next({ q: 'AAPL,MSFT,GOOGL' });
    expect(component.symbols()).toEqual(['AAPL', 'MSFT', 'GOOGL']);
  });

  it('should handle empty query param', () => {
    queryParams$.next({});
    expect(component.symbols()).toEqual([]);
  });

  it('should trim whitespace from symbols', () => {
    queryParams$.next({ q: ' AAPL , MSFT ' });
    expect(component.symbols()).toEqual(['AAPL', 'MSFT']);
  });

  it('should filter out empty strings', () => {
    queryParams$.next({ q: 'AAPL,,MSFT,' });
    expect(component.symbols()).toEqual(['AAPL', 'MSFT']);
  });

  it('should handle single symbol', () => {
    queryParams$.next({ q: 'AAPL' });
    expect(component.symbols()).toEqual(['AAPL']);
  });

  it('should navigate with updated query params on updateSymbols', () => {
    component.updateSymbols(['TSLA', 'AMZN']);
    expect(mockRouter.navigate).toHaveBeenCalledWith([], {
      relativeTo: expect.anything(),
      queryParams: { q: 'TSLA,AMZN' },
      queryParamsHandling: 'merge',
    });
  });

  it('should read interval from query params', () => {
    queryParams$.next({ q: 'AAPL', interval: '2025-01-01_2025-06-01' });
    expect(component.intervalInDates()).toBe('2025-01-01_2025-06-01');
    expect(component.useIntervalInDates()).toBe(true);
  });

  it('should clear share url on destroy', () => {
    component.ngOnDestroy();
    expect(mockShareUrlService.update).toHaveBeenCalledWith({ title: '', url: '' });
  });

  it('should format interval dates when interval contains underscore', () => {
    queryParams$.next({ q: 'AAPL', interval: '2025-01-01_2025-06-01' });
    const formatted = component.formattedInterval();
    expect(formatted.from).toBeTruthy();
    expect(formatted.to).toBeTruthy();
  });

  it('should return empty formatted interval when no underscore', () => {
    queryParams$.next({ q: 'AAPL', interval: 'invalid' });
    const formatted = component.formattedInterval();
    expect(formatted.from).toBe('');
    expect(formatted.to).toBe('');
  });

  it('should expose isProduction flag', () => {
    expect(typeof component.isProduction).toBe('boolean');
  });
});
