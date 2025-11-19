import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PageTerms } from './page-terms';

describe('PageTerms', () => {
  let component: PageTerms;
  let fixture: ComponentFixture<PageTerms>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PageTerms]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PageTerms);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
