import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environments';
import { AuthService } from './auth.service';

export interface PortaleAlloggiConfig {
    portale_username: string;
    portale_password?: string;
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

export interface PortaleAlloggiStatus {
    portale_alloggi_sent: boolean;
    portale_alloggi_sent_at: string | null;
    portale_alloggi_response: string | null;
}

export interface PortaleAlloggiSubmissionResponse {
    message: string;
    result?: any;
    submission_tracked?: boolean;
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
     * Send guest data from a reservation to Portale Alloggi (TEST MODE)
     * @param reservationId The ID of the reservation to send
     * @returns Observable with the submission results
     */
    sendReservationDataTest(reservationId: number): Observable<PortaleAlloggiSubmissionResponse> {
        return this.http.post<PortaleAlloggiSubmissionResponse>(
            `${environment.apiBaseUrl}/api/v1/admin/reservations/${reservationId}/send-to-portale-alloggi`,
            {},
            { headers: this.authService.getAuthHeaders() }
        );
    }

    /**
     * Send guest data from a reservation to Portale Alloggi (REAL PRODUCTION)
     * @param reservationId The ID of the reservation to send
     * @returns Observable with the submission results
     */
    sendReservationDataReal(reservationId: number): Observable<PortaleAlloggiSubmissionResponse> {
        return this.http.post<PortaleAlloggiSubmissionResponse>(
            `${environment.apiBaseUrl}/api/v1/admin/reservations/${reservationId}/send-to-portale-alloggi-real`,
            {},
            { headers: this.authService.getAuthHeaders() }
        );
    }

    /**
     * Get the Portale Alloggi submission status for a reservation
     * @param reservationId The ID of the reservation
     * @returns Observable with the status information
     */
    getSubmissionStatus(reservationId: number): Observable<PortaleAlloggiStatus> {
        return this.http.get<PortaleAlloggiStatus>(
            `${environment.apiBaseUrl}/api/v1/admin/reservations/${reservationId}/portale-alloggi-status`,
            { headers: this.authService.getAuthHeaders() }
        );
    }
}
