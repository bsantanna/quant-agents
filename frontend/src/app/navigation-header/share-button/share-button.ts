import {Component, inject, signal} from '@angular/core';
import {ShareUrlService} from '../../services/share-url-service';

@Component({
  selector: 'app-share-button',
  imports: [],
  templateUrl: './share-button.html',
  styleUrl: './share-button.scss',
})
export class ShareButton {

  private readonly shareUrlService = inject(ShareUrlService);
  readonly shareUrl = this.shareUrlService.shareUrl;
  readonly showMenu = signal<boolean>(false);
  readonly showCopied = signal<boolean>(false);

  toggleMenu() {
    this.showMenu.update((val) => !val);
  }

  share(platform: string) {
    this.showMenu.set(false);
    const currentShareUrl = this.shareUrl();
    const url = encodeURIComponent(currentShareUrl.url);
    const text = encodeURIComponent(currentShareUrl.title);
    let targetUrl: string;

    switch (platform) {
      case 'facebook':
        targetUrl = `https://www.facebook.com/sharer.php?u=${url}`;
        break;
      case 'x':
        targetUrl = `https://twitter.com/intent/tweet?url=${url}&text=${text}`;
        break;
      case 'whatsapp':
        targetUrl = `https://api.whatsapp.com/send?text=${text}%20${url}`;
        break;
      case 'threads':
        targetUrl = `https://www.threads.net/intent/post?text=${text}&url=${url}`;
        break;
      case 'linkedin':
        targetUrl = `https://www.linkedin.com/shareArticle?url=${url}&title=${text}`;
        break;
      case 'reddit':
        targetUrl = `https://reddit.com/submit?url=${url}&title=${text}`;
        break;
      case 'email':
        targetUrl = `mailto:?subject=Quaks&body=${text}%20${url}`;
        window.location.href = targetUrl;
        return; // No new tab for email
      case 'copy':
        navigator.clipboard.writeText(url);
        this.showCopied.set(true);
        setTimeout(() => this.showCopied.set(false), 3000);
        return;
      default:
        return;
    }

    window.open(targetUrl, '_blank');
  }

}
