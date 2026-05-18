import {
  Component,
  DestroyRef,
  PLATFORM_ID,
  afterNextRender,
  inject,
  input,
  signal,
} from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

export interface TocItem {
  id: string;
  label: string;
  level?: 1 | 2;
}

@Component({
  selector: 'app-table-of-contents',
  imports: [],
  templateUrl: './table-of-contents.html',
  styleUrl: './table-of-contents.scss',
})
export class TableOfContents {
  readonly items = input.required<TocItem[]>();
  readonly title = input<string>('On this page');

  readonly activeId = signal<string | null>(null);

  private readonly platformId = inject(PLATFORM_ID);
  private readonly destroyRef = inject(DestroyRef);
  private observer: IntersectionObserver | null = null;

  constructor() {
    afterNextRender(() => this.setupObserver());
    this.destroyRef.onDestroy(() => this.observer?.disconnect());
  }

  scrollTo(event: Event, id: string): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }
    event.preventDefault();
    const target = document.getElementById(id);
    if (!target) {
      return;
    }
    if (typeof target.scrollIntoView === 'function') {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    const url = globalThis.location.pathname + globalThis.location.search + '#' + id;
    history.replaceState(null, '', url);
    this.activeId.set(id);
  }

  private setupObserver(): void {
    if (!isPlatformBrowser(this.platformId) || typeof IntersectionObserver === 'undefined') {
      return;
    }
    const ids = this.items().map((i) => i.id);
    const elements = ids
      .map((id) => document.getElementById(id))
      .filter((el): el is HTMLElement => el !== null);

    if (elements.length === 0) {
      return;
    }

    const visible = new Set<string>();
    this.observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            visible.add(entry.target.id);
          } else {
            visible.delete(entry.target.id);
          }
        }
        for (const id of ids) {
          if (visible.has(id)) {
            this.activeId.set(id);
            return;
          }
        }
      },
      { rootMargin: '-80px 0px -55% 0px', threshold: 0 },
    );

    for (const el of elements) {
      this.observer.observe(el);
    }
  }
}
