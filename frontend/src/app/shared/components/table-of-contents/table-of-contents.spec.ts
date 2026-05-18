import { PLATFORM_ID } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TableOfContents, TocItem } from './table-of-contents';

describe('TableOfContents', () => {
  let fixture: ComponentFixture<TableOfContents>;
  let component: TableOfContents;

  const items: TocItem[] = [
    { id: 'a', label: 'Alpha' },
    { id: 'b', label: 'Beta', level: 2 },
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TableOfContents],
    }).compileComponents();

    fixture = TestBed.createComponent(TableOfContents);
    fixture.componentRef.setInput('items', items);
    fixture.detectChanges();
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('renders one link per item with the right href', () => {
    const links = fixture.nativeElement.querySelectorAll('.toc__link');
    expect(links.length).toBe(items.length);
    expect(links[0].getAttribute('href')).toBe('#a');
    expect(links[1].getAttribute('href')).toBe('#b');
  });

  it('applies the level-2 indent class', () => {
    const liNodes = fixture.nativeElement.querySelectorAll('.toc__item');
    expect(liNodes[0].classList.contains('toc__item--level-2')).toBe(false);
    expect(liNodes[1].classList.contains('toc__item--level-2')).toBe(true);
  });

  it('marks the active item when activeId matches', () => {
    component.activeId.set('b');
    fixture.detectChanges();
    const activeLinks = fixture.nativeElement.querySelectorAll('.toc__link--active');
    expect(activeLinks.length).toBe(1);
    expect(activeLinks[0].textContent.trim()).toBe('Beta');
  });

  it('scrolls to a target id and updates activeId on click', () => {
    const target = document.createElement('div');
    target.id = 'a';
    const scrollSpy = jest.fn();
    (target as unknown as { scrollIntoView: jest.Mock }).scrollIntoView = scrollSpy;
    document.body.appendChild(target);

    const event = new Event('click', { cancelable: true });
    component.scrollTo(event, 'a');

    expect(scrollSpy).toHaveBeenCalledWith({ behavior: 'smooth', block: 'start' });
    expect(component.activeId()).toBe('a');
    expect(event.defaultPrevented).toBe(true);

    document.body.removeChild(target);
  });

  it('ignores scrollTo for unknown ids without throwing', () => {
    const event = new Event('click', { cancelable: true });
    expect(() => component.scrollTo(event, 'does-not-exist')).not.toThrow();
  });

  it('skips scrollIntoView when the target lacks the method', () => {
    const target = document.createElement('div');
    target.id = 'no-scroll';
    (target as unknown as { scrollIntoView: undefined }).scrollIntoView = undefined;
    document.body.appendChild(target);

    const event = new Event('click', { cancelable: true });
    expect(() => component.scrollTo(event, 'no-scroll')).not.toThrow();
    expect(component.activeId()).toBe('no-scroll');

    document.body.removeChild(target);
  });
});

describe('TableOfContents with rendered targets', () => {
  let fixture: ComponentFixture<TableOfContents>;
  let component: TableOfContents;
  let observerCallback: IntersectionObserverCallback | null;
  let observedElements: Element[];
  let disconnectSpy: jest.Mock;
  let originalIO: typeof IntersectionObserver | undefined;
  let targetA: HTMLDivElement;
  let targetB: HTMLDivElement;

  const items: TocItem[] = [
    { id: 'a', label: 'Alpha' },
    { id: 'b', label: 'Beta' },
  ];

  beforeEach(async () => {
    targetA = document.createElement('div');
    targetA.id = 'a';
    targetB = document.createElement('div');
    targetB.id = 'b';
    document.body.appendChild(targetA);
    document.body.appendChild(targetB);

    observerCallback = null;
    observedElements = [];
    disconnectSpy = jest.fn();
    originalIO = (globalThis as { IntersectionObserver?: typeof IntersectionObserver })
      .IntersectionObserver;

    (globalThis as unknown as { IntersectionObserver: unknown }).IntersectionObserver =
      jest.fn((cb: IntersectionObserverCallback) => {
        observerCallback = cb;
        return {
          observe: (el: Element) => observedElements.push(el),
          disconnect: disconnectSpy,
          unobserve: jest.fn(),
          takeRecords: jest.fn(),
        };
      });

    await TestBed.configureTestingModule({
      imports: [TableOfContents],
    }).compileComponents();

    fixture = TestBed.createComponent(TableOfContents);
    fixture.componentRef.setInput('items', items);
    fixture.detectChanges();
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  afterEach(() => {
    document.body.removeChild(targetA);
    document.body.removeChild(targetB);
    if (originalIO === undefined) {
      delete (globalThis as { IntersectionObserver?: typeof IntersectionObserver })
        .IntersectionObserver;
    } else {
      (globalThis as unknown as { IntersectionObserver: typeof IntersectionObserver })
        .IntersectionObserver = originalIO;
    }
  });

  it('observes each rendered target element', () => {
    expect(observedElements).toHaveLength(2);
    expect(observedElements).toContain(targetA);
    expect(observedElements).toContain(targetB);
  });

  it('sets activeId to the first visible item in item order', () => {
    expect(observerCallback).not.toBeNull();
    observerCallback!(
      [
        { target: targetB, isIntersecting: true } as unknown as IntersectionObserverEntry,
      ],
      {} as IntersectionObserver,
    );
    expect(component.activeId()).toBe('b');

    observerCallback!(
      [
        { target: targetA, isIntersecting: true } as unknown as IntersectionObserverEntry,
      ],
      {} as IntersectionObserver,
    );
    expect(component.activeId()).toBe('a');
  });

  it('drops elements from the visible set when they stop intersecting', () => {
    observerCallback!(
      [
        { target: targetA, isIntersecting: true } as unknown as IntersectionObserverEntry,
        { target: targetB, isIntersecting: true } as unknown as IntersectionObserverEntry,
      ],
      {} as IntersectionObserver,
    );
    expect(component.activeId()).toBe('a');

    observerCallback!(
      [
        { target: targetA, isIntersecting: false } as unknown as IntersectionObserverEntry,
      ],
      {} as IntersectionObserver,
    );
    expect(component.activeId()).toBe('b');
  });

  it('disconnects the observer when the component is destroyed', () => {
    fixture.destroy();
    expect(disconnectSpy).toHaveBeenCalled();
  });
});

describe('TableOfContents without matching DOM targets', () => {
  let fixture: ComponentFixture<TableOfContents>;
  let constructorSpy: jest.Mock;
  let originalIO: typeof IntersectionObserver | undefined;

  beforeEach(async () => {
    constructorSpy = jest.fn(() => ({
      observe: jest.fn(),
      disconnect: jest.fn(),
      unobserve: jest.fn(),
      takeRecords: jest.fn(),
    }));
    originalIO = (globalThis as { IntersectionObserver?: typeof IntersectionObserver })
      .IntersectionObserver;
    (globalThis as unknown as { IntersectionObserver: unknown }).IntersectionObserver =
      constructorSpy;

    await TestBed.configureTestingModule({
      imports: [TableOfContents],
    }).compileComponents();

    fixture = TestBed.createComponent(TableOfContents);
    fixture.componentRef.setInput('items', [
      { id: 'no-target-in-dom', label: 'Missing' },
    ] as TocItem[]);
    fixture.detectChanges();
    await fixture.whenStable();
  });

  afterEach(() => {
    if (originalIO === undefined) {
      delete (globalThis as { IntersectionObserver?: typeof IntersectionObserver })
        .IntersectionObserver;
    } else {
      (globalThis as unknown as { IntersectionObserver: typeof IntersectionObserver })
        .IntersectionObserver = originalIO;
    }
  });

  it('does not construct an observer when no items resolve to DOM nodes', () => {
    expect(constructorSpy).not.toHaveBeenCalled();
    expect(fixture.componentInstance).toBeTruthy();
  });
});

describe('TableOfContents on a server platform', () => {
  let fixture: ComponentFixture<TableOfContents>;
  let component: TableOfContents;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TableOfContents],
      providers: [{ provide: PLATFORM_ID, useValue: 'server' }],
    }).compileComponents();

    fixture = TestBed.createComponent(TableOfContents);
    fixture.componentRef.setInput('items', [{ id: 'a', label: 'Alpha' }] as TocItem[]);
    fixture.detectChanges();
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('scrollTo is a no-op on the server', () => {
    const event = new Event('click', { cancelable: true });
    component.scrollTo(event, 'a');
    expect(event.defaultPrevented).toBe(false);
    expect(component.activeId()).toBeNull();
  });
});
