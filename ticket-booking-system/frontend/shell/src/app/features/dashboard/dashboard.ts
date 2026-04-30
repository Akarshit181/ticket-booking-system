import { Component } from '@angular/core';

@Component({
  standalone: true,
  template: `
    <h1>Dashboard ✅</h1>
    <button (click)="logout()">Logout</button>
  `
})
export class DashboardComponent {
  logout() {
    localStorage.removeItem('token');
    window.location.href = '/login';
  }
}