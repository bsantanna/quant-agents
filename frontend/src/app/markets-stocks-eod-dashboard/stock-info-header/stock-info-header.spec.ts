import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StockInfoHeader } from './stock-info-header';

describe('StockInfoHeader', () => {
  let component: StockInfoHeader;
  let fixture: ComponentFixture<StockInfoHeader>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StockInfoHeader]
    })
    .compileComponents();

    fixture = TestBed.createComponent(StockInfoHeader);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
