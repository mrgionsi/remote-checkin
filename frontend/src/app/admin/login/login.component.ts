import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AdminLoginService } from '../../services/admin-login.service'; // importa il servizio
import { Router } from '@angular/router';

@Component({
  selector: 'app-login',
  imports: [FormsModule, CommonModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export class LoginComponent {
  username: string = '';
  password: string = '';
  showPassword = false;
  errorMessage: string | null = null;

  constructor(
    private adminLoginService: AdminLoginService,
    private router: Router
  ) { }

  onLogin() {
    this.errorMessage = null;
    this.adminLoginService.login(this.username, this.password).subscribe({
      next: (res) => {
        console.log(res)
        // Salva il token dove preferisci (es: localStorage)
        localStorage.setItem('user', JSON.stringify(res.user));
        localStorage.setItem('admin_token', res.access_token);
        // Naviga alla home admin o dove vuoi
        this.router.navigate(['/admin/dashboard']);
      },
      error: (err) => {
        this.errorMessage = err.error?.error || 'Errore di autenticazione';
      }
    });
  }
}
