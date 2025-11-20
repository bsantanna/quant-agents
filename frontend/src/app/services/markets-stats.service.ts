import {Injectable} from '@angular/core';
import {environment} from '../environments/environment';
import {HttpClient} from '@angular/common/http';
import {StatsClose} from '../models/markets.model';
import {catchError, Observable, of, timeout} from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class MarketsStatsService {

  private readonly marketsStatsCloseUrl = `${environment.apiBaseUrl}/markets/stats_close`;

  static readonly INITIAL_STATS_CLOSE = {
    key_ticker: '',
    most_recent_close: 0,
    most_recent_date: '',
    percent_variance: 0,
  };

  constructor(private http: HttpClient) {
  }

  getStatsClose(
    indexName: string,
    ticker: string,
    requestTimeoutMs = 10000
  ): Observable<StatsClose> {

    const url = `${this.marketsStatsCloseUrl}/${encodeURIComponent(indexName)}/${encodeURIComponent(ticker)}`;

    return this.http.get<StatsClose>(url).pipe(
      timeout(requestTimeoutMs),
      catchError((error) => {
        console.error(`Failed to fetch latest close for ${ticker} @ ${indexName}`, error);
        return of(MarketsStatsService.INITIAL_STATS_CLOSE);
      })
    );

  }

}
