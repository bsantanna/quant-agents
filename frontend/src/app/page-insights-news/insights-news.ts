import {Component, inject} from '@angular/core';
import {BriefingsList} from '../shared/components/briefings-list/briefings-list';
import {SeoService} from '../shared';

@Component({
  selector: 'app-insights-news',
  imports: [BriefingsList],
  templateUrl: './insights-news.html',
  styleUrl: './insights-news.scss',
})
export class InsightsNews {
  readonly indexName = 'quaks_insights-news';
  readonly sharePathPrefix = '/insights/news/item';

  constructor() {
    inject(SeoService).update({
      title: 'News Briefings',
      description: 'Daily AI-generated investor briefings on market events, earnings, and economic indicators.',
      path: '/insights/news',
    });
  }
}
