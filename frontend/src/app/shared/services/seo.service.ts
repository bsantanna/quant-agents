import {inject, Injectable, signal} from '@angular/core';
import {Meta, Title} from '@angular/platform-browser';
import {DOCUMENT} from '@angular/common';
import {NavigationStart, Router} from '@angular/router';
import {filter} from 'rxjs';

const BASE_URL = 'https://quaks.ai';
const DEFAULT_DESCRIPTION = 'AI-powered financial agents platform for real-time market data analysis, stock insights, technical indicators, and financial news.';
const DEFAULT_IMAGE = `${BASE_URL}/logo_large.png`;

export interface SeoConfig {
  title: string;
  description?: string;
  path?: string;
  image?: string;
  eyebrow?: string;
}

export interface NewsArticleSchema {
  headline: string;
  description: string;
  datePublished: string;
  image?: string;
  author: string;
  url: string;
}

@Injectable({providedIn: 'root'})
export class SeoService {
  private readonly meta = inject(Meta);
  private readonly title = inject(Title);
  private readonly doc = inject(DOCUMENT);
  private readonly router = inject(Router, {optional: true});

  private readonly _pageTitle = signal<string | null>(null);
  private readonly _pageEyebrow = signal<string | null>(null);
  readonly pageTitle = this._pageTitle.asReadonly();
  readonly pageEyebrow = this._pageEyebrow.asReadonly();

  constructor() {
    const events = this.router?.events;
    if (events) {
      events
        .pipe(filter((e): e is NavigationStart => e instanceof NavigationStart))
        .subscribe(() => {
          this._pageTitle.set(null);
          this._pageEyebrow.set(null);
        });
    }
  }

  update(config: SeoConfig): void {
    const fullTitle = `${config.title} | Quaks`;
    const description = config.description ?? DEFAULT_DESCRIPTION;
    const url = `${BASE_URL}${config.path ?? '/'}`;
    const image = config.image ?? DEFAULT_IMAGE;

    this.title.setTitle(fullTitle);
    this.meta.updateTag({name: 'description', content: description});

    // Open Graph
    this.meta.updateTag({property: 'og:title', content: fullTitle});
    this.meta.updateTag({property: 'og:description', content: description});
    this.meta.updateTag({property: 'og:url', content: url});
    this.meta.updateTag({property: 'og:image', content: image});

    // Twitter Card
    this.meta.updateTag({name: 'twitter:title', content: fullTitle});
    this.meta.updateTag({name: 'twitter:description', content: description});
    this.meta.updateTag({name: 'twitter:image', content: image});

    // Canonical
    let link: HTMLLinkElement | null = this.doc.querySelector('link[rel="canonical"]');
    if (!link) {
      link = this.doc.createElement('link');
      link.setAttribute('rel', 'canonical');
      this.doc.head.appendChild(link);
    }
    link.setAttribute('href', url);

    // BreadcrumbList
    this.setBreadcrumbs(config.title, config.path);

    // Visible page-header signals (consumed by NavigationHeader)
    this._pageTitle.set(config.title);
    this._pageEyebrow.set(config.eyebrow ?? null);
  }

  setNewsArticleSchema(article: NewsArticleSchema): void {
    this.removeJsonLd();
    const script = this.doc.createElement('script');
    script.type = 'application/ld+json';
    script.id = 'seo-jsonld';
    script.textContent = JSON.stringify({
      '@context': 'https://schema.org',
      '@type': 'NewsArticle',
      headline: article.headline,
      description: article.description,
      datePublished: article.datePublished,
      image: article.image || undefined,
      author: {'@type': 'Organization', name: article.author},
      publisher: {'@type': 'Organization', name: 'Quaks', logo: {'@type': 'ImageObject', url: DEFAULT_IMAGE}},
      mainEntityOfPage: {'@type': 'WebPage', '@id': article.url},
    });
    this.doc.head.appendChild(script);
  }

  private setBreadcrumbs(title: string, path?: string): void {
    this.doc.getElementById('seo-breadcrumbs')?.remove();
    if (!path || path === '/') return;

    const segments = path.split('/').filter(Boolean);
    const items: {name: string; url: string}[] = [{name: 'Home', url: BASE_URL}];

    let accumulated = '';
    for (let i = 0; i < segments.length - 1; i++) {
      accumulated += `/${segments[i]}`;
      items.push({
        name: segments[i].charAt(0).toUpperCase() + segments[i].slice(1),
        url: `${BASE_URL}${accumulated}`,
      });
    }
    items.push({name: title, url: `${BASE_URL}${path}`});

    const script = this.doc.createElement('script');
    script.type = 'application/ld+json';
    script.id = 'seo-breadcrumbs';
    script.textContent = JSON.stringify({
      '@context': 'https://schema.org',
      '@type': 'BreadcrumbList',
      itemListElement: items.map((item, i) => ({
        '@type': 'ListItem',
        position: i + 1,
        name: item.name,
        item: item.url,
      })),
    });
    this.doc.head.appendChild(script);
  }

  private removeJsonLd(): void {
    this.doc.getElementById('seo-jsonld')?.remove();
  }

  reset(): void {
    this.removeJsonLd();
    this.doc.getElementById('seo-breadcrumbs')?.remove();
    this.update({title: 'AI-Powered Quantitative Finance Platform'});
    this._pageTitle.set(null);
    this._pageEyebrow.set(null);
  }
}
