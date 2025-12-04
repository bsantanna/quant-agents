import {Component, HostListener, inject, signal} from '@angular/core';
import {ShareUrlService} from '../../services/share-url.service';
import {FeedbackMessageService} from '../../services/feedback-message.service';

@Component({
  selector: 'app-share-button',
  imports: [],
  templateUrl: './share-button.html',
  styleUrl: './share-button.scss',
})
export class ShareButtonComponent {

  private readonly shareUrlService = inject(ShareUrlService);
  private readonly feedbackMessageService = inject(FeedbackMessageService);
  readonly shareUrl = this.shareUrlService.state;
  readonly showMenu = signal<boolean>(false);

  toggleMenu() {
    this.showMenu.update((val) => !val);
  }

  share(platform: string) {
    this.showMenu.set(false);
    const currentShareUrl = this.shareUrl();
    const urlEncoded = encodeURIComponent(currentShareUrl.url);
    const text = encodeURIComponent(currentShareUrl.title);
    let targetUrl: string;

    switch (platform) {
      case 'facebook':
        targetUrl = `https://www.facebook.com/sharer.php?u=${urlEncoded}`;
        break;
      case 'x':
        targetUrl = `https://twitter.com/intent/tweet?url=${urlEncoded}&text=${text}`;
        break;
      case 'whatsapp':
        targetUrl = `https://api.whatsapp.com/send?text=${text}%20${urlEncoded}`;
        break;
      case 'threads':
        targetUrl = `https://www.threads.net/intent/post?text=${text}&url=${urlEncoded}`;
        break;
      case 'linkedin':
        targetUrl = `https://www.linkedin.com/shareArticle?url=${urlEncoded}&title=${text}`;
        break;
      case 'reddit':
        targetUrl = `https://reddit.com/submit?url=${urlEncoded}&title=${text}`;
        break;
      case 'email':
        targetUrl = `mailto:?subject=Quaks&body=${text}%20${urlEncoded}`;
        window.location.href = targetUrl;
        return; // No new tab for email
      case 'copy':
        navigator.clipboard.writeText(currentShareUrl.url);
        this.feedbackMessageService.update({
          message: 'Link copied',
          type: 'info',
          timeout: 3000,
        });
        return; // No new tab for clipboard copy
      default:
        return;
    }

    window.open(targetUrl, '_blank');
  }

  @HostListener('document:click', ['$event'])
  @HostListener('document:touchstart', ['$event'])
  onDocumentClick(event: Event) {
    const target = event.target as HTMLElement;
    if (!target.closest('app-share-button')) {
      this.showMenu.set(false);
    }
  }

}
