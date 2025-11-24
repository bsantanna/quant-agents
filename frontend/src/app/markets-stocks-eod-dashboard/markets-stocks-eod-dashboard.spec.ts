import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MarketsStocksEodDashboard } from './markets-stocks-eod-dashboard';

describe('MarketsStocksEodDashboard', () => {
  let component: MarketsStocksEodDashboard;
  let fixture: ComponentFixture<MarketsStocksEodDashboard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarketsStocksEodDashboard]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MarketsStocksEodDashboard);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
