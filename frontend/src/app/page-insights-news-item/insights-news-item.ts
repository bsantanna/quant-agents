import {Component, computed, effect, inject, OnDestroy, PLATFORM_ID, signal} from '@angular/core';
import {ActivatedRoute, ParamMap, Router} from '@angular/router';
import {isPlatformBrowser} from '@angular/common';
import {toSignal} from '@angular/core/rxjs-interop';
import {take} from 'rxjs';
import {MarketsInsightsService} from '../shared/services/markets-insights.service';
import {IndexedKeyTickerService} from '../shared/services/indexed-key-ticker.service';
import {DateFormatService, ShareUrlService, SeoService} from '../shared';
import {InsightsNewsItem as InsightsNewsItemModel} from '../shared/models/markets.model';
import {
  ensureInsightsPrintStyle,
  formatInsightsDate,
  removeInsightsPrintStyle,
  sanitizeInsightsReportHtml,
} from '../shared/utils/content-format.utils';

@Component({
  selector: 'app-insights-news-item',
  imports: [],
  templateUrl: './insights-news-item.html',
  styleUrl: './insights-news-item.scss',
})
export class InsightsNewsItem implements OnDestroy {

  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly insightsService = inject(MarketsInsightsService);
  private readonly tickerService = inject(IndexedKeyTickerService);
  private readonly shareUrlService = inject(ShareUrlService);
  private readonly seoService = inject(SeoService);
  readonly dateFormatService = inject(DateFormatService);
  private tickerSet: Set<string> | null = null;

  private readonly paramMap = toSignal<ParamMap>(this.route.paramMap);
  readonly indexName = computed(() => this.paramMap()?.get('indexName') ?? '');
  readonly newsItemId = computed(() => this.paramMap()?.get('newsItemId') ?? '');
  readonly item = signal<InsightsNewsItemModel | null>(null);
  readonly loading = signal(true);

  constructor() {
    effect(() => {
      const indexName = this.indexName();
      const id = this.newsItemId();
      if (!indexName || !id || !this.isBrowser) return;

      this.insightsService.getInsightsNewsItem(indexName, id)
        .pipe(take(1))
        .subscribe(result => {
          if (result.items.length > 0) {
            const fetched = result.items[0];
            fetched.report_html = sanitizeInsightsReportHtml(fetched.report_html, this.getTickerSet());
            this.item.set(fetched);

            const title = fetched.executive_summary || 'Quaks Briefing';
            const path = this.router.url;
            this.shareUrlService.update({
              title,
              url: `${globalThis.location.origin}${path}`,
            });
            this.seoService.update({title, path});
          }
          this.loading.set(false);
        });
    });
  }

  ngOnDestroy(): void {
    this.shareUrlService.update({title: '', url: ''});
    this.seoService.reset();
    removeInsightsPrintStyle(document);
  }

  downloadPdf(): void {
    if (!this.isBrowser) return;

    ensureInsightsPrintStyle(document);
    const cleanup = () => removeInsightsPrintStyle(document);
    globalThis.addEventListener('afterprint', cleanup, {once: true});
    globalThis.print();
  }

  formatDate(dateStr: string): string {
    return formatInsightsDate(dateStr, value => this.dateFormatService.format(value));
  }

  private getTickerSet(): Set<string> {
    this.tickerSet ??= new Set(
      this.tickerService.indexedKeyTickers().map(t => t.key_ticker)
    );
    return this.tickerSet;
  }
}
