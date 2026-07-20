import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { API_ENDPOINTS } from '../constants/api-endpoints';

import { LoginRequest } from '../models/login-request.model';
import { LoginResponse } from '../models/login-response.model';
import { User } from '../models/user.model';

@Injectable({
  providedIn: 'root',
})
export class Auth {
  private readonly http = inject(HttpClient);


  login(request: LoginRequest): Observable<LoginResponse> {
    const body = new HttpParams()
      .set('username', request.email)
      .set('password', request.password);

    return this.http.post<LoginResponse>(
      `${environment.apiUrl}${API_ENDPOINTS.AUTH.LOGIN}`,
      body.toString(),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );
  }

  getCurrentUser(): Observable<User> {
    return this.http.get<User>(
      `${environment.apiUrl}${API_ENDPOINTS.AUTH.ME}`
    );
  }
}