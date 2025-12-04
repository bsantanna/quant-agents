import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CookieConsentDialogComponent } from './cookie-consent-dialog';

describe('CookieConsentDialog', () => {
  let component: CookieConsentDialogComponent;
  let fixture: ComponentFixture<CookieConsentDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CookieConsentDialogComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CookieConsentDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
