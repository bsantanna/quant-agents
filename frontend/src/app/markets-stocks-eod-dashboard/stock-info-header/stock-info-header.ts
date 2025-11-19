import { Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, ParamMap } from '@angular/router';

@Component({
  selector: 'app-stock-info-header',
  imports: [],
  templateUrl: './stock-info-header.html',
  styleUrl: './stock-info-header.scss',
})
export class StockInfoHeader {

  private readonly route = inject(ActivatedRoute);
  private readonly paramMap = toSignal<ParamMap>(this.route.paramMap);
  readonly keyTicker = computed(() => this.paramMap()?.get('keyTicker') ?? '');

}
