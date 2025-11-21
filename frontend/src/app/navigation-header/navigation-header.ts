import {Component, inject, Signal} from '@angular/core';
import {toSignal} from '@angular/core/rxjs-interop';
import {filter, map} from 'rxjs';
import {NavigationEnd, Router} from '@angular/router';

@Component({
  selector: 'app-navigation-header',
  imports: [],
  templateUrl: './navigation-header.html',
  styleUrl: './navigation-header.scss',
})
export class NavigationHeader {

  private readonly router = inject(Router);

  readonly title!: Signal<string>;

  constructor() {
    this.title = toSignal(
      this.router.events.pipe(
        filter((e): e is NavigationEnd => e instanceof NavigationEnd),
        map(() => {
          let route = this.router.routerState.root;
          while (route.firstChild) route = route.firstChild!;
          return (route.snapshot.title as string) || '';
        })
      ),
      { initialValue: '' }
    );
  }

}
