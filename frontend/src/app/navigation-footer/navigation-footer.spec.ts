import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NavigationFooter } from './navigation-footer';

describe('NavigationFooter', () => {
  let component: NavigationFooter;
  let fixture: ComponentFixture<NavigationFooter>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NavigationFooter]
    })
    .compileComponents();

    fixture = TestBed.createComponent(NavigationFooter);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
