import { Routes } from '@angular/router';
import {MarketsStocksEodDashboard} from './markets-stocks-eod-dashboard/markets-stocks-eod-dashboard';

export const routes: Routes = [
  {
    path: 'markets',
    children: [
      {
        path: 'stocks-eod-dashboard/:keyTicker',
        component: MarketsStocksEodDashboard
      }
    ]
  },
  { path: '**', redirectTo: '' }
];
