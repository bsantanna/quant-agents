import {Injectable, signal, WritableSignal} from '@angular/core';
import {NavigationModel, SharedStateService, ShareUrl} from '../models/navigation.models';

@Injectable({
  providedIn: 'root',
})
export class ShareUrlService implements SharedStateService<ShareUrl> {

  readonly state: WritableSignal<ShareUrl> = signal({url: '', title: ''});

  update(newUrl: ShareUrl): void {
    this.state.set(newUrl);
  }

  getPastDateInDays(days: number): string {
    const date = new Date();
    date.setDate(date.getDate() - days);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are 0-based
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`
  }

}
