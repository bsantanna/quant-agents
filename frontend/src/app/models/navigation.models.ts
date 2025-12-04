import {WritableSignal} from '@angular/core';

export interface NavigationModel {
}

export interface SharedStateService {
  state: WritableSignal<NavigationModel>;

  update(newValue: NavigationModel): void;
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
