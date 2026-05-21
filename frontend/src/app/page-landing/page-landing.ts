import {
  Component,
  DestroyRef,
  ElementRef,
  PLATFORM_ID,
  afterNextRender,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {RouterLink} from '@angular/router';
import {SeoService} from '../shared';

interface DuckParticle {
  ox: number;
  oy: number;
  oz: number;
  sx: number;
  sy: number;
  sz: number;
  r: number;
  g: number;
  b: number;
  alpha: number;
  phase: number;
}

type Vec3 = [number, number, number];

const PARTICLE_COUNT = 8500;
const FORMATION_END = 0.25;
const SAMPLE_STEP = 5;
const SVG_RASTER = 440;
const ALPHA_THRESHOLD = 32;
const Z_MIN = 0.015;
const FOCAL = 900;

@Component({
  selector: 'app-page-landing',
  imports: [RouterLink],
  templateUrl: './page-landing.html',
  styleUrl: './page-landing.scss',
})
export class PageLanding {
  readonly step = signal(0);

  private readonly stage = viewChild<ElementRef<HTMLElement>>('stage');
  private readonly canvas = viewChild<ElementRef<HTMLCanvasElement>>('canvas');
  private readonly platformId = inject(PLATFORM_ID);
  private readonly destroyRef = inject(DestroyRef);

  private particles: DuckParticle[] = [];
  private ctx: CanvasRenderingContext2D | null = null;
  private rafId: number | null = null;
  private progress = 0;
  private accentRgb: [number, number, number] = [255, 213, 74];
  private imageAspect = 1;
  private dpr = 1;
  private inView = true;
  private intersectionObserver: IntersectionObserver | null = null;
  private mediaQuery: MediaQueryList | null = null;

  constructor() {
    inject(SeoService).update({
      title: 'Financial Intelligence for AI Agents & Assistants',
      description:
        'Quaks is an MCP server publishing live market news, fundamentals, technical indicators, and portfolio-grade analysis to any AI agent or assistant that speaks the protocol.',
      path: '/',
    });

    afterNextRender(() => this.initStage());
    this.destroyRef.onDestroy(() => this.teardown());
  }

  private initStage(): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }
    const canvasEl = this.canvas()?.nativeElement;
    const stageEl = this.stage()?.nativeElement;
    if (!canvasEl || !stageEl) {
      return;
    }

    const ctx = canvasEl.getContext('2d');
    if (!ctx) {
      return;
    }
    this.ctx = ctx;

    this.accentRgb = this.readAccentColor(stageEl);
    this.mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    this.sampleDuckImage()
      .then(() => {
        this.fitCanvas();
        window.addEventListener('scroll', this.handleScroll, {passive: true});
        window.addEventListener('resize', this.handleResize, {passive: true});
        this.observeStageVisibility(stageEl);
        this.handleScroll();
        if (this.mediaQuery?.matches) {
          this.renderFrame();
          return;
        }
        this.startLoop();
      })
      .catch(() => {});
  }

  private sampleDuckImage(): Promise<void> {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.decoding = 'async';
      img.onload = () => {
        const aspect = img.naturalWidth / img.naturalHeight;
        const w = aspect >= 1 ? SVG_RASTER : Math.round(SVG_RASTER * aspect);
        const h = aspect >= 1 ? Math.round(SVG_RASTER / aspect) : SVG_RASTER;
        const off = document.createElement('canvas');
        off.width = w;
        off.height = h;
        const octx = off.getContext('2d');
        if (!octx) {
          reject(new Error('no offscreen ctx'));
          return;
        }
        octx.drawImage(img, 0, 0, w, h);
        const data = octx.getImageData(0, 0, w, h).data;

        const collected: DuckParticle[] = [];
        let minX = Infinity;
        let maxX = -Infinity;
        let minY = Infinity;
        let maxY = -Infinity;

        for (let y = 0; y < h; y += SAMPLE_STEP) {
          for (let x = 0; x < w; x += SAMPLE_STEP) {
            const i = (y * w + x) * 4;
            if (data[i + 3] < ALPHA_THRESHOLD) continue;

            const ox = (x - w / 2) / h;
            const oy = (y - h / 2) / h;
            const z = this.classifyZ(ox, oy);

            if (ox < minX) minX = ox;
            if (ox > maxX) maxX = ox;
            if (oy < minY) minY = oy;
            if (oy > maxY) maxY = oy;

            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            const a = data[i + 3] / 255;

            const s1 = this.randomScatter();
            collected.push({
              ox,
              oy,
              oz: z,
              sx: s1[0],
              sy: s1[1],
              sz: s1[2],
              r,
              g,
              b,
              alpha: a,
              phase: Math.random() * Math.PI * 2,
            });
            if (z > Z_MIN) {
              const s2 = this.randomScatter();
              collected.push({
                ox,
                oy,
                oz: -z,
                sx: s2[0],
                sy: s2[1],
                sz: s2[2],
                r,
                g,
                b,
                alpha: a * 0.75,
                phase: Math.random() * Math.PI * 2,
              });
            }
          }
        }

        this.imageAspect = maxY > minY ? (maxX - minX) / (maxY - minY) : 1;
        this.particles = this.thinTo(collected, PARTICLE_COUNT);
        resolve();
      };
      img.onerror = () => reject(new Error('image load failed'));
      img.src = '/logo.svg';
    });
  }

  private classifyZ(ox: number, oy: number): number {
    if (ox >= 0.24 && ox <= 0.44) {
      const t = (ox - 0.24) / 0.2;
      const beakR = 0.07 * (1 - t);
      const dy = oy - -0.1;
      if (Math.abs(dy) < beakR) {
        const z2 = beakR * beakR - dy * dy;
        if (z2 > 0) return Math.sqrt(z2);
      }
    }
    if (ox >= -0.42 && ox <= -0.22) {
      const t = (-0.22 - ox) / 0.2;
      const tailR = 0.08 * (1 - t);
      const dy = oy - -0.05;
      if (Math.abs(dy) < tailR) {
        const z2 = tailR * tailR - dy * dy;
        if (z2 > 0) return Math.sqrt(z2);
      }
    }
    const dhx = ox - 0.15;
    const dhy = oy - -0.2;
    const headR2 = 0.17 * 0.17;
    const headD2 = dhx * dhx + dhy * dhy;
    if (headD2 < headR2) {
      return Math.sqrt(headR2 - headD2);
    }
    const dbx = (ox - -0.05) / 0.3;
    const dby = (oy - 0.07) / 0.22;
    const bodySum = dbx * dbx + dby * dby;
    if (bodySum < 1) {
      return 0.24 * Math.sqrt(1 - bodySum);
    }
    return 0.02;
  }

  private thinTo(items: DuckParticle[], limit: number): DuckParticle[] {
    if (items.length <= limit) return items;
    for (let i = items.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      const tmp = items[i];
      items[i] = items[j];
      items[j] = tmp;
    }
    items.length = limit;
    return items;
  }

  private randomScatter(): Vec3 {
    return [
      Math.random() * 5.0 - 2.5,
      Math.random() * 3.2 - 1.6,
      Math.random() * 3.0 - 1.5,
    ];
  }

  private readAccentColor(el: HTMLElement): [number, number, number] {
    const raw = getComputedStyle(el).getPropertyValue('--accent-primary').trim();
    return this.parseColor(raw) ?? [255, 213, 74];
  }

  private parseColor(value: string): [number, number, number] | null {
    if (!value) {
      return null;
    }
    if (value.startsWith('#')) {
      let h = value.slice(1);
      if (h.length === 3) {
        h = h
          .split('')
          .map((c) => c + c)
          .join('');
      }
      if (h.length !== 6) {
        return null;
      }
      const r = parseInt(h.slice(0, 2), 16);
      const g = parseInt(h.slice(2, 4), 16);
      const b = parseInt(h.slice(4, 6), 16);
      if ([r, g, b].some((n) => Number.isNaN(n))) {
        return null;
      }
      return [r, g, b];
    }
    const m = value.match(/rgba?\(([^)]+)\)/);
    if (m) {
      const parts = m[1].split(',').map((p) => parseFloat(p.trim()));
      if (parts.length >= 3 && parts.every((n) => !Number.isNaN(n))) {
        return [parts[0], parts[1], parts[2]];
      }
    }
    return null;
  }

  private fitCanvas(): void {
    const canvasEl = this.canvas()?.nativeElement;
    if (!canvasEl || !this.ctx) {
      return;
    }
    this.dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = canvasEl.clientWidth;
    const h = canvasEl.clientHeight;
    canvasEl.width = Math.max(1, Math.floor(w * this.dpr));
    canvasEl.height = Math.max(1, Math.floor(h * this.dpr));
    this.ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
  }

  private observeStageVisibility(stageEl: HTMLElement): void {
    if (typeof IntersectionObserver === 'undefined') {
      return;
    }
    this.intersectionObserver = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          this.inView = entry.isIntersecting;
        }
        if (this.inView && !this.rafId && !this.mediaQuery?.matches) {
          this.startLoop();
        }
      },
      {threshold: 0},
    );
    this.intersectionObserver.observe(stageEl);
  }

  private handleScroll = (): void => {
    const stageEl = this.stage()?.nativeElement;
    if (!stageEl) {
      return;
    }
    const track = stageEl.firstElementChild as HTMLElement | null;
    if (!track) {
      return;
    }
    const rect = track.getBoundingClientRect();
    const vh = window.innerHeight;
    const span = rect.height - vh;
    if (span <= 0) {
      this.progress = 0;
      this.step.set(0);
      return;
    }
    const p = Math.max(0, Math.min(1, -rect.top / span));
    this.progress = p;
    const next = Math.min(3, Math.floor(p * 4));
    if (next !== this.step()) {
      this.step.set(next);
    }
  };

  private handleResize = (): void => {
    this.fitCanvas();
    this.handleScroll();
    if (this.mediaQuery?.matches) {
      this.renderFrame();
    }
  };

  private startLoop(): void {
    if (this.rafId !== null) {
      return;
    }
    const tick = (): void => {
      if (!this.inView) {
        this.rafId = null;
        return;
      }
      this.renderFrame();
      this.rafId = requestAnimationFrame(tick);
    };
    this.rafId = requestAnimationFrame(tick);
  }

  private renderFrame(): void {
    const ctx = this.ctx;
    const canvasEl = this.canvas()?.nativeElement;
    if (!ctx || !canvasEl) {
      return;
    }
    const w = canvasEl.clientWidth;
    const h = canvasEl.clientHeight;
    if (w === 0 || h === 0) {
      return;
    }

    ctx.globalCompositeOperation = 'destination-out';
    ctx.fillStyle = 'rgba(0, 0, 0, 0.22)';
    ctx.fillRect(0, 0, w, h);
    ctx.globalCompositeOperation = 'lighter';

    const p = this.progress;
    const easeInOut = p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
    const formProgress = Math.min(1, p / FORMATION_END);
    const formEase = formProgress * formProgress * (3 - 2 * formProgress);
    const driftAmp = (1 - formEase) * 0.06;

    const rotY = (p * 2 - 1) * 0.436;
    const tilt = Math.sin(p * Math.PI) * 0.175;
    const baseFit = Math.min(h * 0.72, (w * 0.55) / this.imageAspect);
    const zoom = 0.55 + Math.sin(p * Math.PI) * 0.55 + easeInOut * 0.15;
    const drawScale = baseFit * zoom;

    const cx = w / 2 + Math.sin(p * Math.PI * 2) * w * 0.04;
    const cy = h * 0.48 + Math.sin(p * Math.PI) * -h * 0.04;

    const cosY = Math.cos(rotY);
    const sinY = Math.sin(rotY);
    const cosX = Math.cos(tilt);
    const sinX = Math.sin(tilt);

    const t = performance.now() * 0.0007;

    for (let i = 0; i < this.particles.length; i++) {
      const pt = this.particles[i];
      const breath = Math.sin(t + pt.phase) * 0.005;
      const driftX = Math.sin(t * 0.4 + pt.phase * 1.7) * driftAmp;
      const driftY = Math.cos(t * 0.35 + pt.phase * 1.3) * driftAmp * 0.7;
      const driftZ = Math.sin(t * 0.45 + pt.phase * 2.1) * driftAmp * 0.5;
      const x0 = pt.sx + (pt.ox - pt.sx) * formEase + breath + driftX;
      const y0 = pt.sy + (pt.oy - pt.sy) * formEase + breath * 0.5 + driftY;
      const z0 = pt.sz + (pt.oz - pt.sz) * formEase + driftZ;

      const x1 = x0 * cosY + z0 * sinY;
      const z1 = -x0 * sinY + z0 * cosY;
      const y2 = y0 * cosX - z1 * sinX;
      const z2 = y0 * sinX + z1 * cosX;

      const persp = FOCAL / (FOCAL + z2 * drawScale * 0.55);
      const px = cx + x1 * drawScale * persp;
      const py = cy + y2 * drawScale * persp;
      const size = Math.max(0.7, 1.6 * persp * (0.85 + easeInOut * 0.35));
      const a = pt.alpha * persp * (0.55 + easeInOut * 0.35);

      ctx.fillStyle = `rgba(${pt.r}, ${pt.g}, ${pt.b}, ${a})`;
      ctx.beginPath();
      ctx.arc(px, py, size, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  private teardown(): void {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    this.intersectionObserver?.disconnect();
    this.intersectionObserver = null;
    if (isPlatformBrowser(this.platformId)) {
      window.removeEventListener('scroll', this.handleScroll);
      window.removeEventListener('resize', this.handleResize);
    }
  }
}
