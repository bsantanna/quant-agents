import {Component, inject, Signal} from '@angular/core';
import {toSignal} from '@angular/core/rxjs-interop';
import {filter, map} from 'rxjs';
import {NavigationEnd, Router} from '@angular/router';
import {StockAutocompleteComponent} from '../components/stock-autocomplete/stock-autocomplete';
import {IndexedKeyTicker} from '../models/markets.model';

@Component({
  selector: 'app-navigation-header',
  imports: [StockAutocompleteComponent],
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
    if(indexedKeyTicker.index.startsWith('quant-agents_stocks-eod')) {
      this.router.navigate(['/markets/stocks-eod-dashboard', indexedKeyTicker.key_ticker]);
    }
  }

}
