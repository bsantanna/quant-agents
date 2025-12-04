import {Injectable, signal, WritableSignal} from '@angular/core';
import {FeedbackMessage, SharedStateService} from '../models/navigation.models';

@Injectable({
  providedIn: 'root',
})
export class FeedbackMessageService implements SharedStateService<FeedbackMessage> {

  static readonly INITIAL_FEEDBACK_MESSAGE: FeedbackMessage = {
    message: '',
    type: 'info',
    timeout: 0,
  };

  readonly state: WritableSignal<FeedbackMessage> = signal(FeedbackMessageService.INITIAL_FEEDBACK_MESSAGE);

  update(newMessage: FeedbackMessage): void {
    this.state.set(newMessage);
    setTimeout(() => this.state.set(FeedbackMessageService.INITIAL_FEEDBACK_MESSAGE), 3000);
  }

}
