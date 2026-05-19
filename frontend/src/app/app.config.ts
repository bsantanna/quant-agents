import { ApplicationConfig, provideBrowserGlobalErrorListeners, provideZonelessChangeDetection } from '@angular/core';
import {provideRouter, TitleStrategy} from '@angular/router';

import { routes } from './app.routes';
import {provideHttpClient, withInterceptors} from '@angular/common/http';
import {authInterceptor} from './shared/interceptors/auth.interceptor';
import { provideClientHydration, withEventReplay } from '@angular/platform-browser';
import {QuaksTitleStrategy} from './shared/services/quaks-title-strategy';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZonelessChangeDetection(),
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])), provideClientHydration(withEventReplay()),
    {provide: TitleStrategy, useClass: QuaksTitleStrategy},
  ]
};
