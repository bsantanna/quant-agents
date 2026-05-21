import {inject, Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Observable} from 'rxjs';
import {environment} from '../../../environments/environment';

export interface SignupRequest {
  email: string;
  first_name: string;
  last_name: string;
  username: string;
}

export interface SignupResponse {
  status: string;
}

@Injectable({providedIn: 'root'})
export class SignupService {
  private readonly http = inject(HttpClient);
  private readonly url = `${environment.apiBaseUrl}/waitlist`;

  register(payload: SignupRequest): Observable<SignupResponse> {
    return this.http.post<SignupResponse>(this.url, payload);
  }
}
