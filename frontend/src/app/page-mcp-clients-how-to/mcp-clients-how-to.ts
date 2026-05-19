import {Component, inject} from '@angular/core';
import {RouterLink} from '@angular/router';
import {SeoService} from '../shared';
import {TableOfContents, TocItem} from '../shared/components/table-of-contents/table-of-contents';

@Component({
  selector: 'app-mcp-clients-how-to',
  imports: [RouterLink, TableOfContents],
  templateUrl: './mcp-clients-how-to.html',
  styleUrl: './mcp-clients-how-to.scss',
})
export class McpClientsHowTo {
  readonly tocItems: TocItem[] = [
    {id: 'what-is-mcp', label: 'What is MCP'},
    {id: 'what-quaks-exposes', label: 'What Quaks exposes'},
    {id: 'what-is-skill', label: 'What is a Skill'},
    {id: 'skills-vs-mcp', label: 'How skills and MCP work together'},
    {id: 'use-via-skills', label: 'Use the workflows via skills'},
    {id: 'customize-prompts', label: 'Customize prompts'},
    {id: 'choose-client', label: 'Choose your client'},
  ];

  constructor() {
    inject(SeoService).update({
      title: 'MCP Clients Overview',
      description: 'How to use Quaks via the Model Context Protocol — install the plugin in your AI agent and run financial-analysis workflows.',
      path: '/mcp-clients/how-to',
    });
  }
}
