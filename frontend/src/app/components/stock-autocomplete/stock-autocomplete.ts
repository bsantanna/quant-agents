import { Component, signal, computed, inject, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {IndexedKeyTicker} from '../../models/markets.model';


@Component({
  selector: 'app-stock-autocomplete',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './stock-autocomplete.html',
  styleUrl: './stock-autocomplete.scss',
})
export class StockAutocompleteComponent {
  searchQuery = signal('');
  isOpen = signal(false);

  // Mocked stock data
  private readonly mockedStocks: IndexedKeyTicker[] = [
    { key_ticker: 'NVDA', index: 'X', name: 'NVIDIA Corporation' },
    { key_ticker: 'GOOG', index: 'X', name: 'Alphabet Inc. (Google)' },
    { key_ticker: 'AAPL', index: 'X', name: 'Apple Inc.' },
    { key_ticker: 'META', index: 'X', name: 'Meta Platforms Inc. (Facebook)' },
    { key_ticker: 'MSFT', index: 'X', name: 'Microsoft Corporation' },
  ];

  // Filtered stocks based on search query
  filteredStocks = computed(() => {
    const query = this.searchQuery().toLowerCase().trim();

    if (!query || query.length === 0) {
      return [];
    }

    return this.mockedStocks.filter(
      (stock) =>
        stock.key_ticker.toLowerCase().includes(query) ||
        stock.name.toLowerCase().includes(query)
    );
  });

  // Output event for when a stock is selected
  stockSelected = output<IndexedKeyTicker>();

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
