import {Component, inject} from '@angular/core';
import {RouterLink} from '@angular/router';
import {SeoService} from '../shared';

@Component({
  selector: 'app-product-features',
  imports: [RouterLink],
  templateUrl: './product-features.html',
  styleUrl: './product-features.scss',
})
export class ProductFeatures {
  constructor() {
    inject(SeoService).update({
      title: 'Features',
      eyebrow: 'Product',
      description: 'The Quaks financial intelligence layer for AI agents — capabilities, surface, and integrations.',
      path: '/product/features',
    });
  }
}
