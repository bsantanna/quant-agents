import {Component, inject} from '@angular/core';
import {RouterLink} from '@angular/router';
import {SeoService} from '../shared';

@Component({
  selector: 'app-page-landing',
  imports: [RouterLink],
  templateUrl: './page-landing.html',
  styleUrl: './page-landing.scss',
})
export class PageLanding {
  constructor() {
    inject(SeoService).update({
      title: 'Financial Intelligence for AI Agents & Assistants',
      description: 'Quaks is an MCP server publishing live market news, fundamentals, technical indicators, and portfolio-grade analysis to any AI agent or assistant that speaks the protocol.',
      path: '/',
    });
  }
}
