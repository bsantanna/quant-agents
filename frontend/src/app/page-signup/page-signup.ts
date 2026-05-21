import {Component, inject, signal} from '@angular/core';
import {FormBuilder, ReactiveFormsModule, Validators} from '@angular/forms';
import {SeoService} from '../shared';
import {SignupService} from '../shared/services/signup.service';

@Component({
  selector: 'app-page-signup',
  imports: [ReactiveFormsModule],
  templateUrl: './page-signup.html',
  styleUrl: './page-signup.scss',
})
export class PageSignup {
  private readonly fb = inject(FormBuilder);
  private readonly signupService = inject(SignupService);

  readonly state = signal<'form' | 'success' | 'duplicate' | 'error'>('form');
  readonly submitting = signal(false);

  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    first_name: ['', Validators.required],
    last_name: ['', Validators.required],
    username: ['', [Validators.required, Validators.minLength(3)]],
  });

  constructor() {
    inject(SeoService).update({
      title: 'Sign Up',
      description: 'Sign up to use the Quaks financial agents platform.',
      path: '/signup',
    });
  }

  submit(): void {
    if (this.form.invalid || this.submitting()) return;
    this.submitting.set(true);
    this.signupService.register(this.form.getRawValue()).subscribe({
      next: () => {
        this.submitting.set(false);
        this.state.set('success');
      },
      error: (err) => {
        this.submitting.set(false);
        if (err?.status === 409) {
          this.state.set('duplicate');
        } else {
          this.state.set('error');
        }
      },
    });
  }
}
