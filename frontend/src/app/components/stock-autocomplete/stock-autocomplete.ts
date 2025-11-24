import {Component, signal, computed, inject, output, Signal} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {HttpClient} from '@angular/common/http';
import {IndexedKeyTicker} from '../../models/markets.model';
import {toSignal} from '@angular/core/rxjs-interop';


@Component({
  selector: 'app-stock-autocomplete',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './stock-autocomplete.html',
  styleUrl: './stock-autocomplete.scss',
})
export class StockAutocompleteComponent {
  private readonly httpClient = inject(HttpClient);

  readonly searchQuery = signal('');
  readonly isOpen = signal(false);
  readonly indexedKeyTickers!: Signal<IndexedKeyTicker[]>;

  // Filtered stocks based on search query
  filteredStocks = computed(() => {
    const query = this.searchQuery().toLowerCase().trim();

    if (!query || query.length === 0) {
      return [];
    }

    return this.indexedKeyTickers().filter(
      (stock) =>
        (stock.key_ticker.toLowerCase().includes(query) || stock.name.toLowerCase().includes(query)) && stock.index.startsWith('quant-agents_stocks-eod')
    );
  });

  // Output event for when a stock is selected
  stockSelected = output<IndexedKeyTicker>();

  constructor() {
    const indexedKeyTickers$ = this.httpClient.get<IndexedKeyTicker[]>('/json/indexed_key_ticker_list.json');
    this.indexedKeyTickers = toSignal(indexedKeyTickers$, {initialValue: []});
  }

  onSearch(event: Event): void {
    const target = event.target as HTMLInputElement;
    this.searchQuery.set(target.value);
    this.isOpen.set(target.value.length > 0);
  }

  onInputFocus(): void {
    if (this.searchQuery().length > 0) {
      this.isOpen.set(true);
    }
  }

  onInputBlur(): void {
    // Delay to allow click on dropdown item to register
    setTimeout(() => {
      this.isOpen.set(false);
    }, 200);
  }

  onSelectStock(stock: IndexedKeyTicker): void {
    this.searchQuery.set(stock.key_ticker);
    this.isOpen.set(false);
    this.stockSelected.emit(stock);
  }

  onClearSearch(): void {
    this.searchQuery.set('');
    this.isOpen.set(false);
  }

}
