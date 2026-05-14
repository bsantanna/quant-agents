import {Component, HostListener, inject, signal} from '@angular/core';
import {Router} from '@angular/router';

@Component({
  selector: 'app-mcp-dropdown',
  imports: [],
  templateUrl: './mcp-dropdown.html',
  styleUrl: './mcp-dropdown.scss',
})
export class McpDropdownComponent {
  private readonly router = inject(Router);
  readonly showMenu = signal(false);

  toggleMenu(): void {
    this.showMenu.update(v => !v);
  }

  navigate(path: string): void {
    this.router.navigate([path]);
    this.showMenu.set(false);
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: Event): void {
    const target = event.target as HTMLElement;
    if (!target.closest('app-mcp-dropdown')) {
      this.showMenu.set(false);
    }
  }
}
