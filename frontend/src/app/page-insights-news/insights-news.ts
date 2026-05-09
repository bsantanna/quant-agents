import {Component} from '@angular/core';
import {BriefingsList} from '../shared/components/briefings-list/briefings-list';

@Component({
  selector: 'app-insights-news',
  imports: [BriefingsList],
  templateUrl: './insights-news.html',
  styleUrl: './insights-news.scss',
})
export class InsightsNews {
  readonly indexName = 'quaks_insights-news';
  readonly sharePathPrefix = '/insights/news/item';
}
