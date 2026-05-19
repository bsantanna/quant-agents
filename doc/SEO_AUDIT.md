# SEO Audit Report — Quaks Platform

**Date:** 2026-05-19 (update 7)
**Previous Audit:** 2026-05-14 (update 6)
**Estimated Lighthouse SEO Score:** ~97/100 (up from ~88 — all critical regressions and high-priority gaps resolved)

---

## Status Summary

| Severity | Open | Closed (this update) |
|---|---|---|
| Critical | 0 | R1 (duplicate H1), R2 (MCP SEO metadata) |
| High | 0 | #25 (sitemap), #26 (stub content, already resolved) |
| Medium | 1 (#19 partial — SSR for dynamic routes) | #20 (TitleStrategy), #24 (page-terms theming, already resolved), #27 (Claude H2, no-op after R1), #28 (Insights SeoService) |
| Low | 0 | #13 (aria-hidden), #18 (hreflang, closed as N/A) |

---

## Resolved (Update 7 — 2026-05-19)

### R1 — Duplicate H1 per page → Fixed

**Approach:** Single H1 site-wide via `<app-page-header>` in the nav header, driven by a reactive title channel.

- `SeoService` publishes `pageTitle` and `pageEyebrow` signals on `update()`; `clearDynamicTitle()` is called by `NavigationHeader` on each `NavigationStart`, so per-page titles never leak between routes.
- `NavigationHeader` computed title = `seo.pageTitle() ?? route.snapshot.title`. Same pattern for eyebrow.
- Affected per-page templates have their `<h1>` demoted to `<h2>` (visual hierarchy preserved): `page-waitlist.html` (3 states), `account-profile.html` (error state), `markets-news-item.component.html`, `insights-profile.html`, `insights-agents-personal.html`.
- Dynamic-title pages publish via `SeoService.update()`: news-item sets the headline; insights-profile sets the agent name (newly added — also fixes #28 for this page); insights-personal sets the agent name dynamically.

### R2 — MCP-clients pages missing SEO metadata → Fixed

`McpClientsHowTo`, `McpClientsClaude`, `McpClientsHermes` all call `SeoService.update()` in their constructors with route-appropriate title, description, OG, canonical, and breadcrumb metadata. Unused `PageHeader` import removed from `mcp-clients-claude.ts`.

### #20 — No TitleStrategy → Fixed

`QuaksTitleStrategy` registered via `{provide: TitleStrategy, useClass: QuaksTitleStrategy}` in `app.config.ts`. It checks `SeoService.pageTitle()` first; when null, it falls back to the route's static `title` and appends ` | Quaks`. Would have caught the recent MCP-clients regression automatically.

### #25 — `/mcp-clients/*` missing from sitemap → Fixed

`how-to`, `claude`, `hermes` added to `frontend/public/sitemap.xml`.

### #28 — Insights pages missing SeoService → Fixed

`InsightsAgents`, `InsightsNews`, `InsightsFinance`, `InsightsProfile` all call `SeoService.update()` now.

### #13 — Decorative imgs without `aria-hidden` → Fixed

Both `<img>` tags in `stock-eod-insights.html` (lines 5 and 25) now pair `alt=""` with `aria-hidden="true"`, matching the established pattern used elsewhere (e.g., the chevron icons in the same component).

### #19 — Static prerender → Expanded (partial)

`app.routes.server.ts` now prerenders 9 public routes: `markets/{stocks,news,performance}`, `mcp-clients/{how-to,claude,hermes}`, `terms`, `privacy`, `waitlist`. Dynamic routes (news item, agent profile, ticker dashboard) and authenticated routes remain client-rendered. Root `/` cannot be prerendered until an explicit `''` route is defined in `app.routes.ts` (currently only reachable via wildcard `redirectTo`).

### Closed without code changes

| # | Status | Reason |
|---|--------|--------|
| #18 | N/A | No i18n planned; `hreflang` not applicable for an English-only product. |
| #24 | Already resolved | `page-terms.html` uses the themed `policy-content` wrapper; no `text-gray-100` present in the current code. Audit was stale. |
| #26 | Already resolved | Hermes and How-to pages have full content with sections, tables, and TOC. Audit was stale (predated the page builds). |
| #27 | No-op | The Claude page emits `<h2>` directly; with R1 resolved (page-header is now the sole H1), this is correct and intentional. |

---

## Still Open

### Medium

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 19 (residual) | **No SSR for dynamic routes** | `news/item/*`, `stocks/:keyTicker`, `profile/*`, `agents/personal/*` | Crawlers still see an empty `<app-root>` for these until JS hydrates. Static prerender now covers the public landing surface; dynamic routes would need per-request SSR (Angular Universal) or a build-time list of known slugs (e.g., top tickers, popular articles). |

---

## What's Working Well

- **SeoService:** Title, description, OG, Twitter, canonical, BreadcrumbList, NewsArticle JSON-LD — per-route. Used in 19 components after this update.
- **Reactive H1 channel:** Single source of truth for the page header. `SeoService.update()` → `pageTitle` signal → `app-page-header` H1 + `<title>` tag, all consistent.
- **TitleStrategy fallback:** Any future route that forgets `SeoService.update()` still gets a sensible browser title.
- **Skip navigation:** Keyboard-accessible skip link to `#main-content`.
- **Structured data:** `WebApplication` on homepage + `NewsArticle` on news item pages with proper cleanup.
- **ARIA attributes:** Well-implemented across components.
- **Image alt text:** Decorative images use `aria-hidden="true" alt=""` consistently.
- **Semantic HTML:** `<main>`, `<nav>`, `<footer>`, `<article>`, `<header>` used correctly.
- **FastAPI SPA fallback:** `StaticFiles(html=True)` for all frontend routes.
- **Path-based routing:** Clean URLs like `/markets/stocks/AAPL`.
- **robots.txt:** Blocks API + internal endpoints, references sitemap.
- **PWA-ready:** Manifest, icons, apple-touch-icon, theme-color.
- **`lang="en"`** on `<html>`.
- **Google Fonts:** Loaded non-blocking with `display=swap`.
- **Static prerender:** 9 public routes shipped as pre-rendered HTML.

---

## Recommended Next Steps

1. **Define an explicit root route** so `/` can be added to the prerender list (currently only `path: '**'` redirects to `''` but `''` isn't an explicit route).
2. **Per-ticker / per-article prerender** — at build time, fetch the top N tickers and recent articles and prerender their pages. Combine with `RenderMode.Prerender` + `getPrerenderParams()`.
3. **Full Angular Universal SSR** — only if dynamic-route SEO turns out to matter (Search Console data will tell).

---

## Key Files

| File | Purpose |
|------|---------|
| `frontend/src/index.html` | Main HTML shell — meta tags, structured data, manifest link |
| `frontend/src/app/app.config.ts` | Angular providers — path routing, QuaksTitleStrategy |
| `frontend/src/app/app.routes.ts` | Route definitions with `title` properties |
| `frontend/src/app/app.routes.server.ts` | Prerender list (9 routes) |
| `frontend/src/app/app.html` | App shell with `<main>` landmark + skip-nav link |
| `frontend/src/app/navigation-header/navigation-header.{ts,html}` | Renders the sole `app-page-header` H1; subscribes to `NavigationStart` to clear the dynamic title |
| `frontend/src/app/shared/components/page-header/page-header.html` | Shared `<h1>` header component |
| `frontend/src/app/shared/services/seo.service.ts` | Dynamic SEO meta tag + JSON-LD service with `pageTitle` / `pageEyebrow` signals |
| `frontend/src/app/shared/services/quaks-title-strategy.ts` | Fallback `<title>` tag manager |
| `frontend/public/sitemap.xml` | 14 URLs total (added `/mcp-clients/*`) |
| `frontend/public/robots.txt` | Allow public pages, block API + internal endpoints |
| `app/main.py` | FastAPI — static files mount with SPA fallback |

## Scoring Targets

| Tool | Current (est.) | Target |
|------|----------------|--------|
| Google Lighthouse SEO | ~97 | 100 |
| Google Lighthouse Accessibility | ~95 | 95+ |
| Google Lighthouse Performance | ~80 | 90+ |
| Google PageSpeed Insights (Mobile) | ~78 | 90+ |
