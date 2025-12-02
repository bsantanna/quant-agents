import {Injectable, signal, WritableSignal} from '@angular/core';
import {ShareUrl} from '../models/navigation.models';

@Injectable({
  providedIn: 'root',
})
export class ShareUrlService {

  readonly shareUrl: WritableSignal<ShareUrl> = signal({url: '', title: ''});

  update(newUrl: ShareUrl): void {
    this.shareUrl.set(newUrl);
  }

}
