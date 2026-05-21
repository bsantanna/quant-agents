import {ComponentFixture, TestBed} from '@angular/core/testing';
import {provideRouter} from '@angular/router';
import {PageLanding} from './page-landing';

describe('PageLanding', () => {
  let fixture: ComponentFixture<PageLanding>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PageLanding],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(PageLanding);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should render the merged hero headline', () => {
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Financial Intelligence.');
    expect(text).toContain('For Everyone.');
  });

  it('should expose the funnel CTAs', () => {
    const el = fixture.nativeElement as HTMLElement;
    const featuresLink = el.querySelector('a[href$="/product/features"]');
    const howItWorksLink = el.querySelector('a[href$="/mcp-clients/how-to"]');
    const signupLink = el.querySelector('a[href$="/signup"]');

    expect(featuresLink).toBeTruthy();
    expect(howItWorksLink).toBeTruthy();
    expect(signupLink).toBeTruthy();
  });
});
