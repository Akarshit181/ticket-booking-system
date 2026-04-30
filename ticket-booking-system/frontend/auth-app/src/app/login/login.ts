import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { AuthService } from '../core/services/auth';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './login.html',
})
export class LoginComponent {

  email = '';
  password = '';
  errorMessage = '';

  constructor(private authService: AuthService) { }

  login() {
    this.authService.login(this.email, this.password).subscribe({
      next: (res: any) => {
        if (res.success) {
          this.authService.setToken(res.access_token);
          window.location.href = 'http://localhost:4200/dashboard';
        } else {
          this.errorMessage = res.message;
        }
      }
    });
  }
}