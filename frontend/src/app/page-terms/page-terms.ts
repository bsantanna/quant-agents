import {Component} from '@angular/core';
import {ShareUrlService} from '../services/share-url-service';

@Component({
  selector: 'app-page-terms',
  imports: [],
  templateUrl: './page-terms.html',
  styleUrl: './page-terms.scss',
})
export class PageTerms {

  constructor(private readonly shareUrlService: ShareUrlService) {
    this.shareUrlService.update({title: '', url: ''});
  }

}
