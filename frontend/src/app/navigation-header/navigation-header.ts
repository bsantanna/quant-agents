import {Component, inject, Signal, signal} from '@angular/core';
import {toSignal} from '@angular/core/rxjs-interop';
import {filter, map} from 'rxjs';
import {NavigationEnd, Router} from '@angular/router';
import {StockAutocompleteComponent} from './stock-autocomplete/stock-autocomplete';
import {IndexedKeyTicker} from '../models/markets.model';
import {STOCK_MARKETS} from '../constants';
import {ShareButton} from './share-button/share-button';

@Component({
  selector: 'app-navigation-header',
  imports: [StockAutocompleteComponent, ShareButton],
  templateUrl: './navigation-header.html',
  styleUrl: './navigation-header.scss',
})
export class NavigationHeader {

  private readonly router = inject(Router);
  readonly title!: Signal<string>;
  readonly path!: Signal<string>;

  constructor() {
    this.title = toSignal(
      this.router.events.pipe(
        filter((e): e is NavigationEnd => e instanceof NavigationEnd),
        map(() => {
          let route = this.router.routerState.root;
          while (route.firstChild) route = route.firstChild!;
          return (route.snapshot.title as string) || '';
        })
      ),
      {initialValue: ''}
    );

    this.path = toSignal(
      this.router.events.pipe(
        filter((e): e is NavigationEnd => e instanceof NavigationEnd),
        map(() => {
          let route = this.router.routerState.root;
          while (route.firstChild) route = route.firstChild!;
          return (route.snapshot.url.join('/') as string) || '';
        })
      ),
      {initialValue: ''}
    );

  }


  onKeyTickerSelected(indexedKeyTicker: IndexedKeyTicker): void {
    if (STOCK_MARKETS.filter(market=> market === indexedKeyTicker.index)) {
      this.router.navigate(['/markets/stocks', indexedKeyTicker.key_ticker]);
    }
  }

}
