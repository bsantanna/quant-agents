import {Component, computed, HostListener, inject, input, OnInit, PLATFORM_ID, signal} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {MarketsInsightsService} from '../../services/markets-insights.service';
import {IndexedKeyTickerService} from '../../services/indexed-key-ticker.service';
import {DateFormatService} from '../../services/date-format.service';
import {FeedbackMessageService} from '../../services/feedback-message.service';
import {InsightsNewsItem} from '../../models/markets.model';
import {take} from 'rxjs';
import {
  applyInsightsAvatarFallback,
  formatInsightsDate,
  getInsightsAgentAvatarSrc,
  sanitizeInsightsReportHtml,
} from '../../utils/content-format.utils';
import {buildShareAction, SharePlatform} from '../../utils/social-share.utils';

@Component({
  selector: 'app-briefings-list',
  imports: [],
  templateUrl: './briefings-list.html',
  styleUrl: './briefings-list.scss',
})
export class BriefingsList implements OnInit {
  readonly indexName = input.required<string>();
  readonly sharePathPrefix = input.required<string>();
  readonly pageSize = input<number>(10);

  private readonly insightsService = inject(MarketsInsightsService);
  private readonly tickerService = inject(IndexedKeyTickerService);
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private tickerSet: Set<string> | null = null;

  readonly dateFormatService = inject(DateFormatService);
  readonly items = signal<InsightsNewsItem[]>([]);
  readonly cursor = signal<string | null>(null);
  readonly loading = signal(false);
  readonly expandedId = signal<string | null>(null);
  readonly loadingReport = signal<string | null>(null);
  readonly hasMore = computed(() => this.cursor() !== null);

  private readonly feedbackMessageService = inject(FeedbackMessageService);
  readonly shareOpenId = signal<string | null>(null);

  ngOnInit(): void {
    if (this.isBrowser) {
      this.fetchList('');
    }
  }

  loadMore(): void {
    const currentCursor = this.cursor();
    if (currentCursor === null || this.loading()) return;
    this.fetchList(currentCursor);
  }

  toggleReport(item: InsightsNewsItem): void {
    if (this.expandedId() === item.id) {
      this.expandedId.set(null);
      return;
    }

    if (item.report_html) {
      this.expandedId.set(item.id);
      return;
    }

    this.loadingReport.set(item.id);
    this.insightsService.getInsightsNewsItem(this.indexName(), item.id)
      .pipe(take(1))
      .subscribe(result => {
        if (result.items.length > 0) {
          const fetched = result.items[0];
          const sanitized = sanitizeInsightsReportHtml(fetched.report_html, this.getTickerSet());
          this.items.update(current =>
            current.map(i => i.id === item.id ? {...i, report_html: sanitized} : i)
          );
        }
        this.expandedId.set(item.id);
        this.loadingReport.set(null);
      });
  }

  private getTickerSet(): Set<string> {
    this.tickerSet ??= new Set(
      this.tickerService.indexedKeyTickers().map(t => t.key_ticker)
    );
    return this.tickerSet;
  }

  toggleShare(itemId: string): void {
    this.shareOpenId.update(id => id === itemId ? null : itemId);
  }

  getShareUrl(item: InsightsNewsItem): string {
    return `${globalThis.location.origin}${this.sharePathPrefix()}/${this.indexName()}/${item.id}`;
  }

  share(platform: SharePlatform, item: InsightsNewsItem): void {
    this.shareOpenId.set(null);
    const action = buildShareAction(platform, {
      url: this.getShareUrl(item),
      title: item.executive_summary || 'Quaks Briefing',
    });
    if (!action) return;

    if (action.kind === 'clipboard') {
      navigator.clipboard.writeText(action.text);
      this.feedbackMessageService.update({message: 'Link copied', type: 'info', timeout: 3000});
      return;
    }

    if (action.kind === 'redirect') {
      globalThis.location.href = action.targetUrl;
      return;
    }

    globalThis.open(action.targetUrl, '_blank');
  }

  @HostListener('document:click', ['$event'])
  @HostListener('document:touchstart', ['$event'])
  onDocumentClick(event: Event): void {
    const target = event.target as HTMLElement;
    if (!target.closest('.briefing-share')) {
      this.shareOpenId.set(null);
    }
  }

  agentAvatarSrc(skillName?: string | null): string {
    return getInsightsAgentAvatarSrc(skillName);
  }

  onAvatarError(event: Event): void {
    applyInsightsAvatarFallback(event.target as HTMLImageElement);
  }

  formatDate(dateStr: string): string {
    return formatInsightsDate(dateStr, value => this.dateFormatService.format(value));
  }

  formatTime(dateStr: string): string {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  private fetchList(cursor: string): void {
    this.loading.set(true);
    this.insightsService.getInsightsNewsList(this.indexName(), this.pageSize(), cursor)
      .pipe(take(1))
      .subscribe(result => {
        this.items.update(current => [...current, ...result.items]);
        this.cursor.set(result.cursor);
        this.loading.set(false);
      });
  }
}
