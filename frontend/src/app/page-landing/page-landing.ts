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
  alpha: number;
  phase: number;
}

type Vec3 = [number, number, number];

interface Triangle {
  a: Vec3;
  b: Vec3;
  c: Vec3;
  alpha: number;
}

const PARTICLE_COUNT = 2800;
const EDGE_RATIO = 0.7;
const FOCAL = 900;
const DUCK_ASPECT = 1.4;

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
    this.particles = this.buildDuckGeometry();

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
  }

  private buildDuckGeometry(): DuckParticle[] {
    const mesh = this.buildDuckMesh();
    const areas = mesh.map((t) => this.triangleArea(t));
    const totalArea = areas.reduce((s, a) => s + a, 0) || 1;
    const perims = mesh.map(
      (t) =>
        this.edgeLength(t.a, t.b) +
        this.edgeLength(t.b, t.c) +
        this.edgeLength(t.c, t.a),
    );
    const totalPerim = perims.reduce((s, p) => s + p, 0) || 1;

    const edgeBudget = Math.floor(PARTICLE_COUNT * EDGE_RATIO);
    const faceBudget = PARTICLE_COUNT - edgeBudget;

    const out: DuckParticle[] = [];
    for (let i = 0; i < mesh.length; i++) {
      const nFace = Math.max(
        1,
        Math.round((faceBudget * areas[i]) / totalArea),
      );
      this.sampleTriangle(out, nFace, mesh[i]);

      const nEdge = Math.max(
        3,
        Math.round((edgeBudget * perims[i]) / totalPerim),
      );
      this.sampleTriangleEdges(out, nEdge, mesh[i]);
    }
    return out;
  }

  private edgeLength(a: Vec3, b: Vec3): number {
    const dx = b[0] - a[0];
    const dy = b[1] - a[1];
    const dz = b[2] - a[2];
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  }

  private sampleTriangleEdges(
    out: DuckParticle[],
    n: number,
    t: Triangle,
  ): void {
    const l1 = this.edgeLength(t.a, t.b);
    const l2 = this.edgeLength(t.b, t.c);
    const l3 = this.edgeLength(t.c, t.a);
    const total = l1 + l2 + l3 || 1;
    const n1 = Math.max(1, Math.round((n * l1) / total));
    const n2 = Math.max(1, Math.round((n * l2) / total));
    const n3 = Math.max(1, n - n1 - n2);
    this.sampleEdge(out, n1, t.a, t.b, t.alpha);
    this.sampleEdge(out, n2, t.b, t.c, t.alpha);
    this.sampleEdge(out, n3, t.c, t.a, t.alpha);
  }

  private sampleEdge(
    out: DuckParticle[],
    n: number,
    a: Vec3,
    b: Vec3,
    alpha: number,
  ): void {
    for (let i = 0; i < n; i++) {
      const u = Math.random();
      const t = Math.random() < 0.5 ? u * u : 1 - u * u;
      out.push({
        ox: a[0] + (b[0] - a[0]) * t,
        oy: a[1] + (b[1] - a[1]) * t,
        oz: a[2] + (b[2] - a[2]) * t,
        alpha: alpha * (0.85 + Math.random() * 0.15),
        phase: Math.random() * Math.PI * 2,
      });
    }
  }

  private buildDuckMesh(): Triangle[] {
    const tris: Triangle[] = [];

    this.addIcosahedron(tris, 0.0, 0.08, 0.0, 0.4, 0.26, 0.28, 0.95, 0.45);
    this.addIcosahedron(tris, 0.2, -0.22, 0.0, 0.18, 0.2, 0.18, 1.0, 0.55);

    this.addPyramid(
      tris,
      [0.52, -0.1, 0.0],
      [
        [0.3, -0.2, 0.0],
        [0.32, -0.12, 0.06],
        [0.3, -0.04, 0.0],
        [0.32, -0.12, -0.06],
      ],
      0.95,
      0.6,
    );

    this.addPyramid(
      tris,
      [-0.48, -0.3, 0.0],
      [
        [-0.3, -0.14, 0.0],
        [-0.28, -0.02, 0.06],
        [-0.3, 0.1, 0.0],
        [-0.28, -0.02, -0.06],
      ],
      0.9,
      0.55,
    );

    tris.push({a: [0.08, -0.04, 0.22], b: [-0.18, 0.02, 0.22], c: [-0.04, 0.16, 0.3], alpha: 1.0});
    tris.push({a: [0.08, -0.04, 0.22], b: [-0.04, 0.16, 0.3], c: [0.1, 0.14, 0.3], alpha: 0.85});
    tris.push({a: [0.08, -0.04, -0.22], b: [-0.04, 0.16, -0.3], c: [-0.18, 0.02, -0.22], alpha: 1.0});
    tris.push({a: [0.08, -0.04, -0.22], b: [0.1, 0.14, -0.3], c: [-0.04, 0.16, -0.3], alpha: 0.85});

    return tris;
  }

  private addIcosahedron(
    out: Triangle[],
    cx: number,
    cy: number,
    cz: number,
    rx: number,
    ry: number,
    rz: number,
    alphaTop: number,
    alphaBot: number,
  ): void {
    const phi = (1 + Math.sqrt(5)) / 2;
    const norm = Math.sqrt(1 + phi * phi);
    const A = 1 / norm;
    const B = phi / norm;
    const nat: Vec3[] = [
      [-A, B, 0], [A, B, 0], [-A, -B, 0], [A, -B, 0],
      [0, -A, B], [0, A, B], [0, -A, -B], [0, A, -B],
      [B, 0, -A], [B, 0, A], [-B, 0, -A], [-B, 0, A],
    ];
    const v: Vec3[] = nat.map((p) => [
      cx + rx * p[0],
      cy - ry * p[1],
      cz + rz * p[2],
    ]);
    const faces: [number, number, number][] = [
      [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
      [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
      [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
      [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
    ];
    for (const [i, j, k] of faces) {
      const avgY = (nat[i][1] + nat[j][1] + nat[k][1]) / 3;
      const tF = (avgY + B) / (2 * B);
      out.push({
        a: v[i],
        b: v[j],
        c: v[k],
        alpha: alphaBot + (alphaTop - alphaBot) * tF,
      });
    }
  }

  private addPyramid(
    out: Triangle[],
    apex: Vec3,
    base: Vec3[],
    alphaSide: number,
    alphaBase: number,
  ): void {
    const n = base.length;
    for (let i = 0; i < n; i++) {
      out.push({a: apex, b: base[i], c: base[(i + 1) % n], alpha: alphaSide});
    }
    for (let i = 1; i < n - 1; i++) {
      out.push({a: base[0], b: base[i + 1], c: base[i], alpha: alphaBase});
    }
  }

  private triangleArea(t: Triangle): number {
    const ux = t.b[0] - t.a[0];
    const uy = t.b[1] - t.a[1];
    const uz = t.b[2] - t.a[2];
    const vx = t.c[0] - t.a[0];
    const vy = t.c[1] - t.a[1];
    const vz = t.c[2] - t.a[2];
    const cx = uy * vz - uz * vy;
    const cy = uz * vx - ux * vz;
    const cz = ux * vy - uy * vx;
    return 0.5 * Math.sqrt(cx * cx + cy * cy + cz * cz);
  }

  private sampleTriangle(out: DuckParticle[], n: number, t: Triangle): void {
    for (let i = 0; i < n; i++) {
      let u = Math.random();
      let v = Math.random();
      if (u + v > 1) {
        u = 1 - u;
        v = 1 - v;
      }
      const w = 1 - u - v;
      out.push({
        ox: t.a[0] * w + t.b[0] * u + t.c[0] * v,
        oy: t.a[1] * w + t.b[1] * u + t.c[1] * v,
        oz: t.a[2] * w + t.b[2] * u + t.c[2] * v,
        alpha: t.alpha * (0.8 + Math.random() * 0.2),
        phase: Math.random() * Math.PI * 2,
      });
    }
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

    const rotY = p * Math.PI * 4;
    const tilt = Math.sin(p * Math.PI) * 0.32;
    const baseFit = Math.min(h * 0.72, (w * 0.55) / DUCK_ASPECT);
    const zoom = 0.55 + Math.sin(p * Math.PI) * 0.55 + easeInOut * 0.15;
    const drawScale = baseFit * zoom;

    const cx = w / 2 + Math.sin(p * Math.PI * 2) * w * 0.04;
    const cy = h * 0.48 + Math.sin(p * Math.PI) * -h * 0.04;

    const cosY = Math.cos(rotY);
    const sinY = Math.sin(rotY);
    const cosX = Math.cos(tilt);
    const sinX = Math.sin(tilt);

    const t = performance.now() * 0.0007;
    const [r, g, b] = this.accentRgb;

    for (let i = 0; i < this.particles.length; i++) {
      const pt = this.particles[i];
      const breath = Math.sin(t + pt.phase) * 0.005;
      const x0 = pt.ox + breath;
      const y0 = pt.oy + breath * 0.5;
      const z0 = pt.oz;

      const x1 = x0 * cosY + z0 * sinY;
      const z1 = -x0 * sinY + z0 * cosY;
      const y2 = y0 * cosX - z1 * sinX;
      const z2 = y0 * sinX + z1 * cosX;

      const persp = FOCAL / (FOCAL + z2 * drawScale * 0.55);
      const sx = cx + x1 * drawScale * persp;
      const sy = cy + y2 * drawScale * persp;
      const size = Math.max(0.7, 1.6 * persp * (0.85 + easeInOut * 0.35));
      const a = pt.alpha * persp * (0.55 + easeInOut * 0.35);

      ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${a})`;
      ctx.beginPath();
      ctx.arc(sx, sy, size, 0, Math.PI * 2);
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
