import {Component, inject, input, Signal} from '@angular/core';
import {MarketsStatsService} from '../../services/markets-stats.service';
import {StatsClose} from '../../models/markets.model';
import {toObservable, toSignal} from '@angular/core/rxjs-interop';
import {combineLatest, switchMap} from 'rxjs';

@Component({
  selector: 'app-stock-info-header',
  imports: [],
  templateUrl: './stock-info-header.html',
  styleUrl: './stock-info-header.scss',
})
export class StockInfoHeader {

  private readonly marketsStatsService = inject(MarketsStatsService);

  indexName = input.required<string>();
  keyTicker = input.required<string>();

  statsClose!: Signal<StatsClose>;

  constructor() {

    const stats$ = combineLatest([
      toObservable(this.indexName),
      toObservable(this.keyTicker)
    ]).pipe(
      switchMap(([index, ticker]) => this.marketsStatsService.getStatsClose(index, ticker))
    );

    this.statsClose = toSignal(stats$, {
      initialValue: MarketsStatsService.INITIAL_STATS_CLOSE
    });
  }

}
