import {Component, inject, Signal, signal} from '@angular/core';
import {toSignal} from '@angular/core/rxjs-interop';
import {filter, map} from 'rxjs';
import {NavigationEnd, Router} from '@angular/router';
import {StockAutocompleteComponent} from './stock-autocomplete/stock-autocomplete';
import {IndexedKeyTicker} from '../models/markets.model';
import {STOCK_MARKETS} from '../constants';
import {ShareUrlService} from '../services/share-url-service';

@Component({
  selector: 'app-navigation-header',
  imports: [StockAutocompleteComponent],
  templateUrl: './navigation-header.html',
  styleUrl: './navigation-header.scss',
})
export class NavigationHeader {

  private readonly router = inject(Router);
  private readonly shareUrlService = inject(ShareUrlService);
  readonly title!: Signal<string>;
  readonly path!: Signal<string>;
  readonly shareUrl = this.shareUrlService.shareUrl;
  readonly showMenu = signal<boolean>(false);
  readonly showCopied = signal<boolean>(false);

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

  toggleMenu() {
    this.showMenu.update((val) => !val);
  }

  share(platform: string) {
    this.showMenu.set(false);
    const currentShareUrl = this.shareUrl();
    const url = encodeURIComponent(currentShareUrl.url);
    const text = encodeURIComponent(currentShareUrl.title);
    let targetUrl: string;

    switch (platform) {
      case 'facebook':
        targetUrl = `https://www.facebook.com/sharer.php?u=${url}`;
        break;
      case 'x':
        targetUrl = `https://twitter.com/intent/tweet?url=${url}&text=${text}`;
        break;
      case 'whatsapp':
        targetUrl = `https://api.whatsapp.com/send?text=${text}%20${url}`;
        break;
      case 'threads':
        targetUrl = `https://www.threads.net/intent/post?text=${text}&url=${url}`;
        break;
      case 'linkedin':
        targetUrl = `https://www.linkedin.com/shareArticle?url=${url}&title=${text}`;
        break;
      case 'reddit':
        targetUrl = `https://reddit.com/submit?url=${url}&title=${text}`;
        break;
      case 'email':
        targetUrl = `mailto:?subject=${text}&body=Check%20out%20this%20page:%20${url}`;
        window.location.href = targetUrl;
        return; // No new tab for email
      case 'copy':
        navigator.clipboard.writeText(url);
        this.showCopied.set(true);
        setTimeout(() => this.showCopied.set(false), 3000);
        return;
      default:
        return;
    }

    window.open(targetUrl, '_blank');
  }

  onKeyTickerSelected(indexedKeyTicker: IndexedKeyTicker): void {
    if (STOCK_MARKETS.filter(market=> market === indexedKeyTicker.index)) {
      this.router.navigate(['/markets/stocks', indexedKeyTicker.key_ticker]);
    }
  }

}
