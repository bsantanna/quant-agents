import { Component } from '@angular/core';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import {DomSanitizer, SafeResourceUrl} from '@angular/platform-browser';


@Component({
  selector: 'app-markets-stocks-eod-dashboard',
  imports: [],
  templateUrl: './markets-stocks-eod-dashboard.html',
  styleUrl: './markets-stocks-eod-dashboard.scss',
})
export class MarketsStocksEodDashboard {
  private readonly route = inject(ActivatedRoute);
  private readonly sanitizer = inject(DomSanitizer);

  private readonly paramMap = toSignal<ParamMap>(this.route.paramMap);
  readonly keyTicker = computed(() => this.paramMap()?.get('keyTicker') ?? '');

  readonly kibanaUrl = computed<SafeResourceUrl>(() => {
    const symbol = encodeURIComponent(this.keyTicker());
    const baseUrl = 'https://kibana.bsantanna.me/app/dashboards';
    const dashboardId = '7d9d4835-fa56-4fd4-97e0-c74399045209';

    const queryParams = new URLSearchParams({
      embed: 'true',
      'show-time-filter': 'true',
      'hide-filter-bar': 'true',
      '_g': '(refreshInterval:(pause:!t,value:60000),time:(from:now-100d,to:now))',
      '_a':`(query:(language:kuery,query:'key_ticker:${symbol}'))`
    });

    const fullUrl = `${baseUrl}?auth_provider_hint=anonymous1#/view/${dashboardId}?${queryParams.toString()}`;
    return this.sanitizer.bypassSecurityTrustResourceUrl(fullUrl);
  });
}
