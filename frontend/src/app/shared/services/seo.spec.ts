import {TestBed} from '@angular/core/testing';
import {Meta, Title} from '@angular/platform-browser';
import {SeoService} from './seo.service';

describe('SeoService', () => {
  let service: SeoService;
  let meta: Meta;
  let title: Title;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(SeoService);
    meta = TestBed.inject(Meta);
    title = TestBed.inject(Title);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should set title with Quaks suffix', () => {
    service.update({title: 'Market News'});
    expect(title.getTitle()).toBe('Market News | Quaks');
  });

  it('should set meta description', () => {
    service.update({title: 'Test', description: 'Custom description'});
    const tag = meta.getTag('name="description"');
    expect(tag?.content).toBe('Custom description');
  });

  it('should use default description when not provided', () => {
    service.update({title: 'Test'});
    const tag = meta.getTag('name="description"');
    expect(tag?.content).toContain('AI-powered financial agents platform');
  });

  it('should set Open Graph tags', () => {
    service.update({title: 'Stocks', description: 'Desc', path: '/markets/stocks'});
    expect(meta.getTag('property="og:title"')?.content).toBe('Stocks | Quaks');
    expect(meta.getTag('property="og:description"')?.content).toBe('Desc');
    expect(meta.getTag('property="og:url"')?.content).toBe('https://quaks.ai/markets/stocks');
    expect(meta.getTag('property="og:image"')?.content).toBe('https://quaks.ai/logo_large.png');
  });

  it('should set Twitter Card tags', () => {
    service.update({title: 'News', description: 'Latest news'});
    expect(meta.getTag('name="twitter:title"')?.content).toBe('News | Quaks');
    expect(meta.getTag('name="twitter:description"')?.content).toBe('Latest news');
    expect(meta.getTag('name="twitter:image"')?.content).toBe('https://quaks.ai/logo_large.png');
  });

  it('should use custom image when provided', () => {
    service.update({title: 'Article', image: 'https://example.com/photo.jpg'});
    expect(meta.getTag('property="og:image"')?.content).toBe('https://example.com/photo.jpg');
    expect(meta.getTag('name="twitter:image"')?.content).toBe('https://example.com/photo.jpg');
  });

  it('should default path to / when not provided', () => {
    service.update({title: 'Home'});
    expect(meta.getTag('property="og:url"')?.content).toBe('https://quaks.ai/');
  });

  it('should set canonical link', () => {
    service.update({title: 'Test', path: '/markets/news'});
    const link = document.querySelector('link[rel="canonical"]');
    expect(link?.getAttribute('href')).toBe('https://quaks.ai/markets/news');
  });

  it('should reuse existing canonical link element', () => {
    service.update({title: 'First', path: '/first'});
    service.update({title: 'Second', path: '/second'});
    const links = document.querySelectorAll('link[rel="canonical"]');
    expect(links.length).toBe(1);
    expect(links[0].getAttribute('href')).toBe('https://quaks.ai/second');
  });

  it('should reset to defaults', () => {
    service.update({title: 'Custom', description: 'Custom desc', path: '/custom'});
    service.reset();
    expect(title.getTitle()).toBe('AI-Powered Quantitative Finance Platform | Quaks');
    expect(meta.getTag('property="og:url"')?.content).toBe('https://quaks.ai/');
  });

  it('should publish pageTitle and pageEyebrow signals on update', () => {
    service.update({title: 'Tesla earnings beat', eyebrow: 'News'});
    expect(service.pageTitle()).toBe('Tesla earnings beat');
    expect(service.pageEyebrow()).toBe('News');
  });

  it('should clear pageTitle and pageEyebrow on reset', () => {
    service.update({title: 'Some title', eyebrow: 'Some eyebrow'});
    service.reset();
    expect(service.pageTitle()).toBeNull();
    expect(service.pageEyebrow()).toBeNull();
  });

  it('should leave pageEyebrow null when eyebrow is not provided', () => {
    service.update({title: 'No eyebrow'});
    expect(service.pageEyebrow()).toBeNull();
  });
});
