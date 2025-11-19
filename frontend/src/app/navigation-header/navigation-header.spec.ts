import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NavigationHeader } from './navigation-header';

describe('NavigationHeader', () => {
  let component: NavigationHeader;
  let fixture: ComponentFixture<NavigationHeader>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NavigationHeader]
    })
    .compileComponents();

    fixture = TestBed.createComponent(NavigationHeader);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
