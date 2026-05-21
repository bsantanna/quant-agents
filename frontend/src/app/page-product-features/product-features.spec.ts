import {ComponentFixture, TestBed} from '@angular/core/testing';
import {provideRouter} from '@angular/router';
import {ProductFeatures} from './product-features';

describe('ProductFeatures', () => {
  let fixture: ComponentFixture<ProductFeatures>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProductFeatures],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(ProductFeatures);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should forward the funnel to pricing', () => {
    const link = (fixture.nativeElement as HTMLElement).querySelector('a[href$="/product/pricing"]');
    expect(link).toBeTruthy();
  });
});
