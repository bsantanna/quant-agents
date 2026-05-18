import { Component } from '@angular/core';
import {RouterLink} from '@angular/router';
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
    {id: 'request-access', label: 'Request access'},
    {id: 'install', label: 'Install in Hermes Agent'},
    {id: 'sign-in', label: 'Sign in on first use'},
    {id: 'manage', label: 'Update & uninstall'},
  ];
}
