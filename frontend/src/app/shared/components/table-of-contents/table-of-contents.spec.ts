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
});
