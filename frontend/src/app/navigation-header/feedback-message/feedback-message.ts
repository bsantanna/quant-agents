import {Component, inject} from '@angular/core';
import {FeedbackMessageService} from '../../services/feedback-message.service';

@Component({
  selector: 'app-feedback-message',
  imports: [],
  templateUrl: './feedback-message.html',
  styleUrl: './feedback-message.scss',
})
export class FeedbackMessageComponent {

  private readonly feedbackMessageService = inject(FeedbackMessageService);
  readonly feedbackMessage = this.feedbackMessageService.state;

}
