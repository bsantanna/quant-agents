import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import {NavigationHeader} from './navigation-header/navigation-header';
import {NavigationFooter} from './navigation-footer/navigation-footer';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, NavigationHeader, NavigationFooter],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  protected readonly title = signal('frontend');
}
