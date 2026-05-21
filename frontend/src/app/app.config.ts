import { ApplicationConfig, provideBrowserGlobalErrorListeners, provideZonelessChangeDetection } from '@angular/core';
import {provideRouter, TitleStrategy, withInMemoryScrolling} from '@angular/router';

import { routes } from './app.routes';
import {provideHttpClient, withInterceptors} from '@angular/common/http';
import {authInterceptor} from './shared/interceptors/auth.interceptor';
import { provideClientHydration, withEventReplay } from '@angular/platform-browser';
import {QuaksTitleStrategy} from './shared/services/quaks-title-strategy';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZonelessChangeDetection(),
    provideRouter(routes, withInMemoryScrolling({anchorScrolling: 'enabled'})),
    provideHttpClient(withInterceptors([authInterceptor])), provideClientHydration(withEventReplay()),
    {provide: TitleStrategy, useClass: QuaksTitleStrategy},
  ]
};
