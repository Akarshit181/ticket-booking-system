import { Routes } from '@angular/router';
import { DashboardComponent } from './features/dashboard/dashboard';
import { authGuard } from './core/guards/auth-guard';


export const routes: Routes = [
    {
        path: '',
        redirectTo: 'login',
        pathMatch: 'full'
    },
    {
        path: 'login',
        loadComponent: () =>
            import('auth/LoginComponent').then(m => m.LoginComponent)
    },
    {
        path: 'dashboard',
        component: DashboardComponent,
        canActivate: [authGuard]   // 🔥 MUST BE HERE
    }
];