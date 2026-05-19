import {TestBed} from '@angular/core/testing';
import {Title} from '@angular/platform-browser';
import {RouterStateSnapshot} from '@angular/router';
import {QuaksTitleStrategy} from './quaks-title-strategy';
import {SeoService} from './seo.service';

class StubStrategy extends QuaksTitleStrategy {
  override buildTitle(_: RouterStateSnapshot): string | undefined {
    return this.stubbed;
  }
  stubbed: string | undefined = undefined;
}

describe('QuaksTitleStrategy', () => {
  let strategy: StubStrategy;
  let title: Title;
  let seo: SeoService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [{provide: QuaksTitleStrategy, useClass: StubStrategy}],
    });
    strategy = TestBed.inject(QuaksTitleStrategy) as StubStrategy;
    title = TestBed.inject(Title);
    seo = TestBed.inject(SeoService);
    seo.reset();
  });

  it('sets title from route data when SeoService has no dynamic title', () => {
    strategy.stubbed = 'Stocks';
    strategy.updateTitle({} as RouterStateSnapshot);
    expect(title.getTitle()).toBe('Stocks | Quaks');
  });

  it('falls back to bare Quaks when route has no title', () => {
    strategy.stubbed = undefined;
    strategy.updateTitle({} as RouterStateSnapshot);
    expect(title.getTitle()).toBe('Quaks');
  });

  it('does not overwrite when SeoService already set a dynamic title', () => {
    seo.update({title: 'Tesla earnings beat'});
    const before = title.getTitle();
    strategy.stubbed = 'Article';
    strategy.updateTitle({} as RouterStateSnapshot);
    expect(title.getTitle()).toBe(before);
    expect(title.getTitle()).toBe('Tesla earnings beat | Quaks');
  });
});
