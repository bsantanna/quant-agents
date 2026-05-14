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

@Component({
  selector: 'app-navigation-header',
  imports: [StockAutocompleteComponent, NewsAutocompleteComponent, ShareButtonComponent, FeedbackMessageComponent, SettingsDropdownComponent, HamburgerMenuComponent, InsightsDropdownComponent, MarketsDropdownComponent, McpDropdownComponent, AuthDropdownComponent],
  templateUrl: './navigation-header.html',
  styleUrl: './navigation-header.scss',
})
export class NavigationHeader implements AfterViewInit, OnDestroy {
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly router = inject(Router);
  readonly subHeader = viewChild<ElementRef>('subHeader');
  readonly stickyVisible = signal(false);
  private observer: IntersectionObserver | null = null;

  private readonly routeInfo: Signal<{ path: string; title: string }> = toSignal(
    this.router.events.pipe(
      filter((e): e is NavigationEnd => e instanceof NavigationEnd),
      startWith(null),
      map(() => {
        let route = this.router.routerState.root;
        while (route.firstChild) route = route.firstChild!;
        return {
          path: this.router.url,
          title: (route.snapshot.title as string) || '',
        };
      })
    ),
    {initialValue: {path: this.router.url, title: ''}}
  );

  readonly path = () => this.routeInfo().path;
  readonly title = () => this.routeInfo().title;

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
