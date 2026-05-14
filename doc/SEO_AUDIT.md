# SEO Audit Report — Quaks Platform

**Date:** 2026-05-14 (update 6)
**Previous Audit:** 2026-04-06 (update 5)
**Estimated Lighthouse SEO Score:** ~88/100 (down from ~96 — see Critical regressions below)

---

## Critical Regressions (Update 6)

Two regressions introduced by the in-progress `fix/hermes-support-12` work — both directly cancel resolved items from earlier updates.

| # | Issue | Location | Severity | Detail |
|---|-------|----------|----------|--------|
| R1 | **Duplicate H1 per page** | `navigation-header.html:68` | Critical | `<app-navigation-header>` now renders `<app-page-header>` which emits `<h1>` from the active route's `title`. Pages that already emit their own `<h1>` now produce 2 H1s. Confirmed regressions: `waitlist`, `account/profile`, `markets/news/item/:…`, `insights/profile/:agentName`, `insights/agents/personal/:agentSlug`. This reopens previously-resolved item #7. |
| R2 | **New routes missing per-page SEO metadata** | `page-mcp-clients-{how-to,claude,hermes}/*.ts` | Critical | None of the three new MCP-clients components inject `SeoService`. Result: shared static title/description/OG/canonical from `index.html` apply to all three routes — Google sees them as duplicates of `/`. Reopens previously-resolved item #4/#5/#9. |

### How to fix R1

Pick one path and apply it consistently:

- **Recommended** — strip `<h1>` from per-page templates and let `<app-page-header>` in nav-header be the single source. Pages whose H1 needs dynamic content (e.g., article title, agent name, ticker symbol) should push that value into the route title via `Router.routerState.root` snapshot or a route-data resolver, then the nav-header picks it up. Affected templates: `page-waitlist/page-waitlist.html` (3 H1s), `page-account-profile/account-profile.html`, `page-markets-news-item/markets-news-item.component.html`, `page-insights-profile/insights-profile.html`, `page-insights-personal/insights-agents-personal.html`.
- **Alternative** — demote `app-page-header`'s element to a non-H1 wrapper and re-introduce H1s in each page template. Reverses the design intent of the new shared header.

### How to fix R2

Inject `SeoService` and call `update()` in `McpClientsHowTo`, `McpClientsClaude`, `McpClientsHermes` constructors / `ngOnInit`. Suggested copy:

```ts
this.seo.update({
  title: 'Use Quaks with Claude',
  description: 'Install the Quaks plugin and connect Claude to your personal financial agents via MCP.',
  path: '/mcp-clients/claude',
});
```

Same pattern for `/mcp-clients/how-to` and `/mcp-clients/hermes` with route-appropriate copy.

---

## New High-Priority Findings (Update 6)

| # | Issue | Location | Severity |
|---|-------|----------|----------|
| 25 | **Sitemap missing `/mcp-clients/*` routes** | `frontend/public/sitemap.xml` | High |
| 26 | **Stub content on Hermes + How-to pages** | `mcp-clients-hermes.html` (`<p>mcp-clients-hermes works!</p>`), `mcp-clients-how-to.html` (`<p>mcp-clients-how-to works!</p>`) | High |
| 27 | **Heading hierarchy on Claude page** | `mcp-clients-claude.html:3` | Medium — page emits `<h2>` directly; relies entirely on nav-header H1. Acceptable once R1 is resolved, but if R1 is fixed by reverting the shared H1, this page will have no H1. |
| 28 | **Other pages still missing `SeoService`** | `page-insights-agents/*`, `page-insights-news/*`, `page-insights-finance/*`, `page-insights-profile/*` | Medium — pre-existing gap, not introduced by this branch, but worth fixing alongside R2. |

---

## Resolved (All Time)

| # | Issue | Resolution |
|---|-------|------------|
| 1 | Hash routing (`/#/`) | `withHashLocation()` removed. Path-based routing active. |
| 2 | No robots.txt | Added to `frontend/public/robots.txt`. |
| 3 | No sitemap.xml | Added to `frontend/public/sitemap.xml` with per-ticker pages. |
| 4 | No meta description | In `index.html` + `SeoService` per route. **Reopened as R2 for MCP-clients routes.** |
| 5 | No Open Graph / Twitter Cards | Full OG + Twitter Card tags, dynamically updated. **Reopened as R2 for MCP-clients routes.** |
| 6 | No structured data (JSON-LD) | `WebApplication` schema in `index.html`. |
| 6b | No per-page structured data for news | `NewsArticle` JSON-LD injected by `SeoService.setNewsArticleSchema()` on news item pages. |
| 6c | No BreadcrumbList schema | `SeoService.update()` auto-generates `BreadcrumbList` JSON-LD from the `path` param. |
| 7 | Multiple H1 tags in nav header | **REOPENED as R1** — shared `app-page-header` in `navigation-header.html` re-introduces H1 in the header, colliding with per-page H1s. |
| 8 | No `<main>` landmark | `<main id="main-content">` wraps router-outlet. |
| 9 | No canonical URLs | `SeoService` dynamically sets `<link rel="canonical">`. **Reopened as R2 for MCP-clients routes.** |
| 10 | Static page title | `SeoService` sets unique `<title>` per route. **Reopened as R2 for MCP-clients routes.** |
| 11 | No `prefers-reduced-motion` CSS | `@media (prefers-reduced-motion: reduce)` at line 118 in `styles.scss`. |
| 12 | No skip-navigation link | `<a href="#main-content" class="sr-only focus:not-sr-only ...">` in `app.html`. |
| 14 | No Web App Manifest | `manifest.webmanifest` with icons (192x192, 512x512). |
| 15 | No favicon set | Full set in `frontend/public/icons/`. |
| 16 | Stub content on Stocks page | Replaced with full heatmap component. |
| 17 | Google Fonts `@import` blocking render | Replaced with `<link rel="preconnect">` + `<link rel="stylesheet">` in `index.html`. |
| 21 | Sitemap incomplete | Insights + waitlist routes added (still missing `/mcp-clients/*` — see #25). |
| 22 | `/cookies` redundant | `/privacy` already contains full cookie policy. |
| 23 | Cookie management UX | Footer button opens consent dialog, links to `/privacy`. |

---

## Still Open

### Medium

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 19 | **No SSR/prerendering** | Entire SPA | Crawlers see empty `<app-root>` until JS runs. Largest remaining SEO uplift. |
| 20 | **No `TitleStrategy`** | `app.config.ts` | Routes that forget `SeoService.update()` fall through to the static `index.html` title. A `TitleStrategy` would auto-apply the route `title` to the document title as a baseline. This is exactly the failure mode behind R2 — implementing it would have caught the new pages automatically. |
| 28 | **Insights pages missing `SeoService`** | `page-insights-{agents,news,finance,profile}/*` | Same problem as R2 for older routes. |
| 24 | **`page-terms.html` hardcoded text colors** | `text-gray-100` | Not theme-aware. |

### Low

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 13 | `stock-eod-insights.html` img `alt=""` without `aria-hidden` | Line 5 | `alt=""` is valid per WCAG for decorative images, but pairing with `aria-hidden="true"` would be cleaner. |
| 18 | No `hreflang` tags | N/A | Only relevant if i18n is planned. |

---

## What's Working Well

- **SeoService**: Title, description, OG, Twitter, canonical, BreadcrumbList, NewsArticle JSON-LD — per-route. Used in 15+ components.
- **Skip navigation**: Keyboard-accessible skip link to `#main-content`.
- **Structured data**: `WebApplication` on homepage + `NewsArticle` on news item pages with proper cleanup.
- **ARIA attributes**: Well-implemented across components.
- **Image alt text**: Good coverage — decorative images use `aria-hidden="true" alt=""`.
- **Semantic HTML**: `<main>`, `<nav>`, `<footer>`, `<article>`, `<header>` used correctly.
- **FastAPI SPA fallback**: `StaticFiles(html=True)` for all frontend routes.
- **Path-based routing**: Clean URLs like `/markets/stocks/AAPL`.
- **robots.txt**: Blocks API + internal endpoints, references sitemap.
- **PWA-ready**: Manifest, icons, apple-touch-icon, theme-color.
- **`lang="en"`**: Present on `<html>` tag.
- **Google Fonts**: Loaded non-blocking, `display=swap`.

---

## Recommended Next Steps (Priority Order)

1. **Fix R1 (duplicate H1)** — Strip per-page H1s and let `app-page-header` be the single source, OR demote the shared header to non-H1. Pick before merging `fix/hermes-support-12`.
2. **Fix R2 (MCP-clients SEO metadata)** — Inject `SeoService` into the three new page components.
3. **Add the missing `/mcp-clients/*` URLs to `sitemap.xml`** (item #25).
4. **Replace stub content on `/mcp-clients/hermes` and `/mcp-clients/how-to`** (item #26) — currently single-`<p>` scaffolds.
5. **Wire up `TitleStrategy`** — Fallback for routes that forget `SeoService` (item #20). Would have prevented R2.
6. **Backfill `SeoService` on remaining Insights pages** (item #28).
7. **Consider SSR/prerendering** — Angular Universal or static prerender for key landing pages.

---

## Key Files

| File | Purpose |
|------|---------|
| `frontend/src/index.html` | Main HTML shell — meta tags, structured data, manifest link |
| `frontend/src/app/app.config.ts` | Angular providers — path routing (no hash) |
| `frontend/src/app/app.routes.ts` | Route definitions with `title` properties |
| `frontend/src/app/app.html` | App shell with `<main>` landmark + skip-nav link |
| `frontend/src/app/navigation-header/navigation-header.html` | Renders shared `app-page-header` (now emits H1 — see R1) |
| `frontend/src/app/shared/components/page-header/page-header.html` | New shared `<h1>` header component |
| `frontend/src/app/shared/services/seo.service.ts` | Dynamic SEO meta tag + JSON-LD service |
| `frontend/public/sitemap.xml` | Missing `/mcp-clients/*` URLs |
| `frontend/public/robots.txt` | Allow public pages, block API + internal endpoints |
| `app/main.py` | FastAPI — static files mount with SPA fallback |

## Scoring Targets

| Tool | Current (est.) | Target |
|------|----------------|--------|
| Google Lighthouse SEO | ~88 | 100 |
| Google Lighthouse Accessibility | ~80 (down from ~85 — duplicate H1 penalty) | 95+ |
| Google Lighthouse Performance | ~80 | 90+ |
| Google PageSpeed Insights (Mobile) | ~75 | 90+ |
