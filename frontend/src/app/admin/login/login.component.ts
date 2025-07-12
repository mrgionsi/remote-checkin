import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AdminLoginService } from '../../services/admin-login.service'; // importa il servizio
import { Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { NgModule } from '@angular/core';
import { ToastModule } from 'primeng/toast';

@Component({
  selector: 'app-login',
  imports: [FormsModule, CommonModule, ToastModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
  providers: [MessageService]
})
export class LoginComponent {
  username: string = '';
  password: string = '';
  showPassword = false;
  errorMessage: string | null = null;

  constructor(
    private adminLoginService: AdminLoginService,
    private router: Router,
    private messageService: MessageService // <--- aggiungi qui
  ) { }

  onLogin() {
    this.errorMessage = null;
    this.adminLoginService.login(this.username, this.password).subscribe({
      next: (res) => {
        localStorage.setItem('user', JSON.stringify(res.user));
        localStorage.setItem('admin_token', res.access_token);
        this.messageService.add({ severity: 'success', summary: 'Login effettuato', detail: 'Benvenuto!' });
        this.router.navigate(['/admin/dashboard']);
      },
      error: (err) => {
        if (err.status === 401) {
          this.messageService.add({ severity: 'error', summary: 'Login fallito', detail: 'Username o password errati.' });
        } else if (err.status === 403) {
          this.messageService.add({ severity: 'warn', summary: 'Non autorizzato', detail: 'Non hai i permessi per accedere.' });
        } else if (err.status === 400) {
          this.messageService.add({ severity: 'warn', summary: 'Dati mancanti', detail: 'Inserisci username e password.' });
        } else {
          this.messageService.add({ severity: 'error', summary: 'Errore', detail: 'Errore di autenticazione. Riprova.' });
        }
        this.errorMessage = err.error?.error || 'Errore di autenticazione';
      }
    });
  }
}
