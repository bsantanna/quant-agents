import {Component, inject} from '@angular/core';
import {RouterLink} from '@angular/router';
import {SeoService} from '../shared';
import {TableOfContents, TocItem} from '../shared/components/table-of-contents/table-of-contents';

@Component({
  selector: 'app-mcp-clients-hermes',
  imports: [RouterLink, TableOfContents],
  templateUrl: './mcp-clients-hermes.html',
  styleUrl: './mcp-clients-hermes.scss',
})
export class McpClientsHermes {
  readonly tocItems: TocItem[] = [
    {id: 'overview', label: 'What you get'},
    {id: 'signup', label: 'Sign up'},
    {id: 'install', label: 'Install in Hermes Agent'},
    {id: 'sign-in', label: 'Sign in on first use'},
    {id: 'manage', label: 'Update & uninstall'},
  ];

  constructor() {
    inject(SeoService).update({
      title: 'Use Quaks with Hermes Agent',
      description: 'Install the Quaks plugin in Hermes Agent and connect to your personal financial agents via MCP.',
      path: '/mcp-clients/hermes',
    });
  }
}
