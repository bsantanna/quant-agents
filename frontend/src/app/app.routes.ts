import { Routes } from '@angular/router';
import {MarketsStocksEodDashboard} from './markets-stocks-eod-dashboard/markets-stocks-eod-dashboard';
import { PageTerms } from './page-terms/page-terms';

export const routes: Routes = [
  {
    title: 'Markets',
    path: 'markets',
    children: [
      {
        title: 'Stocks EoD Dashboard',
        path: 'stocks-eod-dashboard/:keyTicker',
        component: MarketsStocksEodDashboard
      }
    ]
  },
  {
    title: 'Terms of Service',
    path: 'terms',
    component: PageTerms
  },
  { path: '**', redirectTo: '' }
];
