import {ComponentFixture, TestBed} from '@angular/core/testing';

import {PageHeader} from './page-header';

describe('PageHeader', () => {
  let component: PageHeader;
  let fixture: ComponentFixture<PageHeader>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PageHeader]
    }).compileComponents();

    fixture = TestBed.createComponent(PageHeader);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('title', 'Claude');
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('renders title only when eyebrow and subtitle are absent', () => {
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.page-header__title')?.textContent).toContain('Claude');
    expect(host.querySelector('.page-header__eyebrow')).toBeNull();
    expect(host.querySelector('.page-header__subtitle')).toBeNull();
  });

  it('renders eyebrow when provided', () => {
    fixture.componentRef.setInput('eyebrow', 'MCP Client');
    fixture.detectChanges();
    const eyebrow = fixture.nativeElement.querySelector('.page-header__eyebrow');
    expect(eyebrow?.textContent).toContain('MCP Client');
  });

  it('renders subtitle when provided', () => {
    fixture.componentRef.setInput('subtitle', 'Connect your personal agent.');
    fixture.detectChanges();
    const subtitle = fixture.nativeElement.querySelector('.page-header__subtitle');
    expect(subtitle?.textContent).toContain('Connect your personal agent.');
  });

  it('renders all three sections when all inputs provided', () => {
    fixture.componentRef.setInput('eyebrow', 'MCP Client');
    fixture.componentRef.setInput('subtitle', 'Connect your personal agent.');
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.page-header__eyebrow')).not.toBeNull();
    expect(host.querySelector('.page-header__title')).not.toBeNull();
    expect(host.querySelector('.page-header__subtitle')).not.toBeNull();
  });
});
