import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

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
  onLogin() {
    // Qui puoi aggiungere la logica di autenticazione
    console.log('Username:', this.username);
    console.log('Password:', this.password);
  }
}
