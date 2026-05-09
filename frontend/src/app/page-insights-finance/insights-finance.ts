import {Component} from '@angular/core';
import {BriefingsList} from '../shared/components/briefings-list/briefings-list';

@Component({
  selector: 'app-insights-finance',
  imports: [BriefingsList],
  templateUrl: './insights-finance.html',
  styleUrl: './insights-finance.scss',
})
export class InsightsFinance {
  readonly indexName = 'quaks_insights-finance';
  readonly sharePathPrefix = '/insights/financial/item';
}
