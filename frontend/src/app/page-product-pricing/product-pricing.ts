import {Component, inject} from '@angular/core';
import {RouterLink} from '@angular/router';
import {SeoService} from '../shared';

@Component({
  selector: 'app-product-pricing',
  imports: [RouterLink],
  templateUrl: './product-pricing.html',
  styleUrl: './product-pricing.scss',
})
export class ProductPricing {
  constructor() {
    inject(SeoService).update({
      title: 'Pricing',
      eyebrow: 'Product',
      description: 'Quaks pricing plans for individuals, teams, and agent platforms — coming soon.',
      path: '/product/pricing',
    });
  }
}
