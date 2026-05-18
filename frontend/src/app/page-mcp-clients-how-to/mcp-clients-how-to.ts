import { Component } from '@angular/core';
import {RouterLink} from '@angular/router';
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
}
