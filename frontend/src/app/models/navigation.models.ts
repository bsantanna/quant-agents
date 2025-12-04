import {WritableSignal} from '@angular/core';

export interface NavigationModel {
}

export interface SharedStateService<T extends NavigationModel> {
  state: WritableSignal<T>;

  update(newValue: T): void;
}

export interface FeedbackMessage extends NavigationModel {
  message: string;
  type: 'success' | 'info' | 'error' | 'warning' ;
  timeout: number;
}

export interface ShareUrl extends NavigationModel {
  url: string;
  title: string;
}

export interface CookieConsent extends NavigationModel {
  consentGiven: boolean;
  type: 'all' | 'essential_only';
}
