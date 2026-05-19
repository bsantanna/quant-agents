import { RenderMode, ServerRoute } from '@angular/ssr';

export const serverRoutes: ServerRoute[] = [
  {
    path: 'markets/stocks',
    renderMode: RenderMode.Prerender
  },
  {
    path: 'markets/news',
    renderMode: RenderMode.Prerender
  },
  {
    path: 'markets/performance',
    renderMode: RenderMode.Prerender
  },
  {
    path: 'mcp-clients/how-to',
    renderMode: RenderMode.Prerender
  },
  {
    path: 'mcp-clients/claude',
    renderMode: RenderMode.Prerender
  },
  {
    path: 'mcp-clients/hermes',
    renderMode: RenderMode.Prerender
  },
  {
    path: 'terms',
    renderMode: RenderMode.Prerender
  },
  {
    path: 'privacy',
    renderMode: RenderMode.Prerender
  },
  {
    path: 'waitlist',
    renderMode: RenderMode.Prerender
  },
  {
    path: '**',
    renderMode: RenderMode.Client
  }
];
