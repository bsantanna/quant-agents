import { Routes } from '@angular/router';
import {MarketsStocksEodDashboard} from './page-markets-stocks-eod-dashboard/markets-stocks-eod-dashboard';
import { PageTerms } from './page-terms/page-terms';

export const routes: Routes = [
  {
    title: 'Markets',
    path: 'markets',
    children: [
      {
        title: 'Stock Analysis',
        path: 'stocks/:keyTicker',
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
