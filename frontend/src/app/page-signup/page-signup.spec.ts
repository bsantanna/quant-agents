import {ComponentFixture, TestBed} from '@angular/core/testing';
import {PageSignup} from './page-signup';
import {provideHttpClient} from '@angular/common/http';
import {provideHttpClientTesting} from '@angular/common/http/testing';
import {provideRouter} from '@angular/router';

describe('PageSignup', () => {
  let component: PageSignup;
  let fixture: ComponentFixture<PageSignup>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PageSignup],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(PageSignup);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should start in form state', () => {
    expect(component.state()).toBe('form');
  });

  it('should have invalid form when empty', () => {
    expect(component.form.invalid).toBe(true);
  });

  it('should validate email format', () => {
    component.form.controls.email.setValue('invalid');
    expect(component.form.controls.email.invalid).toBe(true);

    component.form.controls.email.setValue('test@example.com');
    expect(component.form.controls.email.valid).toBe(true);
  });

  it('should validate username minimum length', () => {
    component.form.controls.username.setValue('ab');
    expect(component.form.controls.username.invalid).toBe(true);

    component.form.controls.username.setValue('abc');
    expect(component.form.controls.username.valid).toBe(true);
  });

  it('should not submit when form is invalid', () => {
    component.submit();
    expect(component.submitting()).toBe(false);
    expect(component.state()).toBe('form');
  });

  it('should not submit when already submitting', () => {
    component.form.setValue({email: 'a@b.com', first_name: 'A', last_name: 'B', username: 'abc'});
    component.submitting.set(true);
    component.submit();
    expect(component.submitting()).toBe(true);
  });

  it('should submit valid form and transition to success', () => {
    const {HttpTestingController} = jest.requireActual('@angular/common/http/testing');
    const httpTesting = TestBed.inject(HttpTestingController);

    component.form.setValue({email: 'test@test.com', first_name: 'John', last_name: 'Doe', username: 'jdoe'});
    component.submit();
    expect(component.submitting()).toBe(true);

    const req = httpTesting.expectOne((r: any) => r.url.includes('/waitlist'));
    req.flush({});

    expect(component.submitting()).toBe(false);
    expect(component.state()).toBe('success');
  });

  it('should transition to duplicate on 409 error', () => {
    const {HttpTestingController} = jest.requireActual('@angular/common/http/testing');
    const httpTesting = TestBed.inject(HttpTestingController);

    component.form.setValue({email: 'test@test.com', first_name: 'John', last_name: 'Doe', username: 'jdoe'});
    component.submit();

    const req = httpTesting.expectOne((r: any) => r.url.includes('/waitlist'));
    req.flush('Conflict', {status: 409, statusText: 'Conflict'});

    expect(component.submitting()).toBe(false);
    expect(component.state()).toBe('duplicate');
  });

  it('should transition to error on non-409 error', () => {
    const {HttpTestingController} = jest.requireActual('@angular/common/http/testing');
    const httpTesting = TestBed.inject(HttpTestingController);

    component.form.setValue({email: 'test@test.com', first_name: 'John', last_name: 'Doe', username: 'jdoe'});
    component.submit();

    const req = httpTesting.expectOne((r: any) => r.url.includes('/waitlist'));
    req.flush('Error', {status: 500, statusText: 'Server Error'});

    expect(component.submitting()).toBe(false);
    expect(component.state()).toBe('error');
  });
});
