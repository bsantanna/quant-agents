import { RenderMode, ServerRoute } from '@angular/ssr';

export const serverRoutes: ServerRoute[] = [
  {
    path: '',
    renderMode: RenderMode.Prerender
  },
  {
    path: 'product/features',
    renderMode: RenderMode.Prerender
  },
  {
    path: 'product/pricing',
    renderMode: RenderMode.Prerender
  },
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
    path: 'signup',
    renderMode: RenderMode.Prerender
  },
  {
    path: '**',
    renderMode: RenderMode.Client
  }
];
