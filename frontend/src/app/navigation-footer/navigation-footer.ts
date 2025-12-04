import { Component } from '@angular/core';
import {CookieConsentDialogComponent} from './cookie-consent-dialog/cookie-consent-dialog';

@Component({
  selector: 'app-navigation-footer',
  imports: [
    CookieConsentDialogComponent
  ],
  templateUrl: './navigation-footer.html',
  styleUrl: './navigation-footer.scss',
})
export class NavigationFooter {

}
