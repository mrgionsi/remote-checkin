import { Injectable } from '@angular/core';
import { Resolve } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { Observable, of } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AuthResolver implements Resolve<boolean> {
    constructor(private authService: AuthService) { }

    resolve(): Observable<boolean> {
        // Qui puoi fare una chiamata API o controllare localStorage
        // Esempio: ritorna true se autenticato, altrimenti false
        return of(this.authService.isLoggedIn());
    }
}