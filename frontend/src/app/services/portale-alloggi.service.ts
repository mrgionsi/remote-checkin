import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environments';
import { AuthService } from './auth.service';

export interface PortaleAlloggiConfig {
    portale_username: string;
    portale_password: string;
    portale_wskey: string;
}

export interface PortaleAlloggiConfigResponse {
    message: string;
    config: {
        portale_username: string;
        portale_password: string; // This will be masked/empty for security
        portale_wskey: string;
    };
}

export interface PortaleAlloggiTestResponse {
    message: string;
    status: string;
    token_received?: boolean;
    details?: string;
}

@Injectable({
    providedIn: 'root'
})
export class PortaleAlloggiService {
    private apiUrl = `${environment.apiBaseUrl}/api/v1/admin/portale-alloggi`;

    constructor(private http: HttpClient, private authService: AuthService) { }

    /**
     * Get the current Portale Alloggi configuration
     * @returns Observable with the configuration (password will be masked)
     */
    getConfig(): Observable<PortaleAlloggiConfigResponse> {
        return this.http.get<PortaleAlloggiConfigResponse>(
            this.apiUrl,
            { headers: this.authService.getAuthHeaders() }
        );
    }

    /**
     * Update the Portale Alloggi configuration
     * @param config The configuration to save
     * @returns Observable with the response
     */
    saveConfig(config: PortaleAlloggiConfig): Observable<PortaleAlloggiConfigResponse> {
        return this.http.post<PortaleAlloggiConfigResponse>(
            this.apiUrl,
            config,
            { headers: this.authService.getAuthHeaders() }
        );
    }

    /**
     * Test the Portale Alloggi connection with current credentials
     * @returns Observable with the test results
     */
    testConnection(): Observable<PortaleAlloggiTestResponse> {
        return this.http.post<PortaleAlloggiTestResponse>(
            `${this.apiUrl}/test`,
            {},
            { headers: this.authService.getAuthHeaders() }
        );
    }

    /**
     * Send guest data from a reservation to Portale Alloggi
     * @param reservationId The ID of the reservation to send
     * @returns Observable with the submission results
     */
    sendReservationData(reservationId: number): Observable<any> {
        return this.http.post<any>(
            `${environment.apiBaseUrl}/api/v1/admin/reservations/${reservationId}/send-to-portale-alloggi`,
            {},
            { headers: this.authService.getAuthHeaders() }
        );
    }
}
