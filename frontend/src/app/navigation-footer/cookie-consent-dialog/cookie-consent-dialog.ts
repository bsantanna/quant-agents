import {Component, inject} from '@angular/core';
import {CookieService} from '../../services/cookie.service';

@Component({
  selector: 'app-cookie-consent-dialog',
  imports: [],
  templateUrl: './cookie-consent-dialog.html',
  styleUrl: './cookie-consent-dialog.scss',
})
export class CookieConsentDialogComponent {

  private readonly cookieConsentService = inject(CookieService);
  readonly cookieConsent = this.cookieConsentService.state;

  updateConsent(type: 'essential_only' | 'all'): void {
    this.cookieConsentService.update({consentGiven: true, type});
  }

}
