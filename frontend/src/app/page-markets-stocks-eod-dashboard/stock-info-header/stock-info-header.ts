import {Component, inject, Input, input, Signal, WritableSignal} from '@angular/core';
import {MarketsStatsService} from '../../services/markets-stats.service';
import {StatsClose} from '../../models/markets.model';
import {toObservable, toSignal} from '@angular/core/rxjs-interop';
import {combineLatest, switchMap, tap} from 'rxjs';
import {DecimalPipe} from '@angular/common';
import {ShareUrlService} from '../../services/share-url-service';

@Component({
  selector: 'app-stock-info-header',
  imports: [DecimalPipe],
  templateUrl: './stock-info-header.html',
  styleUrl: './stock-info-header.scss',
})
export class StockInfoHeader {

  private readonly marketsStatsService = inject(MarketsStatsService);
  private readonly shareUrlService = inject(ShareUrlService);

  indexName = input.required<string>();
  keyTicker = input.required<string>();
  intervalInDates = input.required<string>();
  useIntervalInDates = input.required<boolean>();

  @Input() intervalInDays!: WritableSignal<number>;

  statsClose!: Signal<StatsClose>;

  constructor() {

    const stats$ = combineLatest([
      toObservable(this.indexName),
      toObservable(this.keyTicker),
      toObservable(this.intervalInDates)
    ]).pipe(
      switchMap(
        ([index, ticker, intervalInDates]) => this.marketsStatsService.getStatsClose(index, ticker, intervalInDates)
      )
    );

    this.statsClose = toSignal(stats$, {
      initialValue: MarketsStatsService.INITIAL_STATS_CLOSE
    });

  }

  setIntervalInDays(days: number): void {
    this.intervalInDays.set(days);
  }

  getPastDateInDays(days: number): string {
    return this.shareUrlService.getPastDateInDays(days);
  }

}
