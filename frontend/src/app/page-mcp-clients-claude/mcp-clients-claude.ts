import {Component, inject} from '@angular/core';
import {RouterLink} from '@angular/router';
import {SeoService} from '../shared';
import {TableOfContents, TocItem} from '../shared/components/table-of-contents/table-of-contents';

@Component({
  selector: 'app-mcp-clients-claude',
  imports: [RouterLink, TableOfContents],
  templateUrl: './mcp-clients-claude.html',
  styleUrl: './mcp-clients-claude.scss',
})
export class McpClientsClaude {
  readonly tocItems: TocItem[] = [
    {id: 'overview', label: 'What you get'},
    {id: 'request-access', label: 'Request access'},
    {id: 'install-cowork', label: 'Install in Claude Cowork'},
    {id: 'install-code', label: 'Install in Claude Code'},
    {id: 'install-manually', label: 'Install manually'},
    {id: 'install-terminal', label: 'From your terminal'},
    {id: 'sign-in', label: 'Sign in on first use'},
    {id: 'manage', label: 'Update, disable & uninstall'},
  ];

  constructor() {
    inject(SeoService).update({
      title: 'Use Quaks with Claude',
      description: 'Install the Quaks plugin and connect Claude Code or Claude Cowork to your personal financial agents via MCP.',
      path: '/mcp-clients/claude',
    });
  }
}
