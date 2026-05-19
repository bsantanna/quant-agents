import {Component, inject} from '@angular/core';
import {BriefingsList} from '../shared/components/briefings-list/briefings-list';
import {SeoService} from '../shared';

@Component({
  selector: 'app-insights-finance',
  imports: [BriefingsList],
  templateUrl: './insights-finance.html',
  styleUrl: './insights-finance.scss',
})
export class InsightsFinance {
  readonly indexName = 'quaks_insights-finance';
  readonly sharePathPrefix = '/insights/financial/item';

  constructor() {
    inject(SeoService).update({
      title: 'Financial Briefings',
      description: 'AI-generated fundamental + technical analysis briefings with BUY/HOLD/SELL signals across a watchlist.',
      path: '/insights/financial',
    });
  }
}
