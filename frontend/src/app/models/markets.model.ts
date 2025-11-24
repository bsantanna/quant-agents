export interface IndexedKeyTicker {
  key_ticker: string;
  index: string;
  name: string;
}

export interface StatsClose {
  key_ticker: string;
  most_recent_close: number;
  most_recent_date: string;
  most_recent_low:number;
  most_recent_high:number;
  most_recent_volume:number;
  most_recent_open:number;
  percent_variance: number;
}
