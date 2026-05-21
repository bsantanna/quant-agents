import {ComponentFixture, TestBed} from '@angular/core/testing';
import {provideRouter} from '@angular/router';
import {ProductPricing} from './product-pricing';

describe('ProductPricing', () => {
  let fixture: ComponentFixture<ProductPricing>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProductPricing],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(ProductPricing);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should forward the funnel to signup', () => {
    const link = (fixture.nativeElement as HTMLElement).querySelector('a[href$="/signup"]');
    expect(link).toBeTruthy();
  });
});
