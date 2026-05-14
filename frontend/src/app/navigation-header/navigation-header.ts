import {AfterViewInit, Component, ElementRef, inject, OnDestroy, PLATFORM_ID, signal, Signal, viewChild} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {StockAutocompleteComponent} from './stock-autocomplete/stock-autocomplete';
import {NewsAutocompleteComponent} from './news-autocomplete/news-autocomplete';
import {IndexedKeyTicker} from '../shared';
import {STOCK_MARKETS} from '../constants';
import {ShareButtonComponent} from './share-button/share-button';
import {InsightsDropdownComponent} from './insights-dropdown/insights-dropdown';
import {MarketsDropdownComponent} from './markets-dropdown/markets-dropdown';
import {McpDropdownComponent} from './mcp-dropdown/mcp-dropdown';
import {FeedbackMessageComponent} from './feedback-message/feedback-message';
import {SettingsDropdownComponent} from './settings-dropdown/settings-dropdown';
import {HamburgerMenuComponent} from './hamburger-menu/hamburger-menu';
import {AuthDropdownComponent} from './auth-dropdown/auth-dropdown';
import {NavigationEnd, Router} from '@angular/router';
import {toSignal} from '@angular/core/rxjs-interop';
import {filter, map, startWith} from 'rxjs';
import {PageHeader} from '../shared/components/page-header/page-header';

@Component({
  selector: 'app-navigation-header',
  imports: [StockAutocompleteComponent, NewsAutocompleteComponent, ShareButtonComponent, FeedbackMessageComponent, SettingsDropdownComponent, HamburgerMenuComponent, InsightsDropdownComponent, MarketsDropdownComponent, McpDropdownComponent, AuthDropdownComponent, PageHeader],
  templateUrl: './navigation-header.html',
  styleUrl: './navigation-header.scss',
})
export class NavigationHeader implements AfterViewInit, OnDestroy {
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly router = inject(Router);
  readonly subHeader = viewChild<ElementRef>('subHeader');
  readonly stickyVisible = signal(false);
  private observer: IntersectionObserver | null = null;

  private readonly routeInfo: Signal<{ path: string; title: string; eyebrow: string }> = toSignal(
    this.router.events.pipe(
      filter((e): e is NavigationEnd => e instanceof NavigationEnd),
      startWith(null),
      map(() => {
        const root = this.router.routerState.root;
        let route = root;
        let parent = root;
        while (route.firstChild) {
          parent = route;
          route = route.firstChild!;
        }
        const eyebrow = parent !== root ? (parent.snapshot.title as string) || '' : '';
        return {
          path: this.router.url,
          title: (route.snapshot.title as string) || '',
          eyebrow,
        };
      })
    ),
    {initialValue: {path: this.router.url, title: '', eyebrow: ''}}
  );

  readonly path = () => this.routeInfo().path;
  readonly title = () => this.routeInfo().title;
  readonly eyebrow = () => this.routeInfo().eyebrow;

  onKeyTickerSelected(indexedKeyTicker: IndexedKeyTicker): void {
    if (STOCK_MARKETS.filter(market => market === indexedKeyTicker.index)) {
      this.router.navigate(['/markets/stocks', indexedKeyTicker.key_ticker]);
    }
  }

  ngAfterViewInit(): void {
    if (!this.isBrowser) return;
    const el = this.subHeader()?.nativeElement;
    if (el) {
      this.observer = new IntersectionObserver(
        ([entry]) => this.stickyVisible.set(!entry.isIntersecting),
        {threshold: 0}
      );
      this.observer.observe(el);
    }
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
  }
}
