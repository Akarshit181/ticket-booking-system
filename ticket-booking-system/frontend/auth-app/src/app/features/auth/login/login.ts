import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { Auth } from '../../../core/services/auth';
import { Token } from '../../../core/services/token';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(Auth);
  private readonly token = inject(Token);
  private readonly router = inject(Router);

  readonly loginForm = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

  login(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.auth.login(this.loginForm.getRawValue()).subscribe({
      next: (response) => {
        console.log('Login successful:', response);

        this.token.setAccessToken(response.access_token);
        this.token.setRefreshToken(response.refresh_token);

        this.router.navigate(['/dashboard']).then((success) => {
          console.log('Navigation success:', success);
        });
      },
      error: (error) => {
        console.error('Login failed:', error);
      },
    });
  }
}