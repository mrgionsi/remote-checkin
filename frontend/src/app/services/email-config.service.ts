import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environments';
import { AuthService } from './auth.service';

export interface EmailConfig {
    id?: number;
    user_id?: number;
    mail_server: string;
    mail_port: number;
    mail_use_tls: boolean;
    mail_use_ssl: boolean;
    mail_username: string;
    mail_password: string;
    mail_default_sender_name: string;
    mail_default_sender_email: string;
    provider_type: string;
    provider_config?: any;
    is_active: boolean;
    created_at?: string;
    updated_at?: string;
}

export interface EmailProviderPreset {
    name: string;
    mail_server: string;
    mail_port: number;
    mail_use_tls: boolean;
    mail_use_ssl: boolean;
    provider_type?: string;
    instructions: string;
}

export interface EmailTestResult {
    status: string;
    message: string;
    result?: any;
}

@Injectable({
    providedIn: 'root'
})
export class EmailConfigService {

    private apiUrl = `${environment.apiBaseUrl}/api/v1`;
    constructor(private http: HttpClient, private authService: AuthService) { }

    /**
     * Get current user's email configuration
     * @param includePassword - If true, returns decrypted password for editing
     */
    getEmailConfig(includePassword: boolean = false): Observable<EmailConfig> {
        const params = includePassword ? '?include_password=true' : '';
        return this.http.get<EmailConfig>(`${this.apiUrl}/email-config${params}`, { headers: this.authService.getAuthHeaders() });
    }

    /**
     * Create or update email configuration
     */
    saveEmailConfig(config: EmailConfig): Observable<any> {
        const payload = { ...config };
        if (payload.mail_password === '***' || payload.mail_password === '') {
            delete (payload as any).mail_password;
        }
        return this.http.post(
            `${this.apiUrl}/email-config`,
            payload,
            { headers: this.authService.getAuthHeaders() }
        );
    }

    /**
     * Test email configuration
     */
    testEmailConfig(testEmail: string): Observable<EmailTestResult> {
        return this.http.post<EmailTestResult>(`${this.apiUrl}/email-config/test`, {
            test_email: testEmail
        }, { headers: this.authService.getAuthHeaders() });
    }

    /**
     * Get available email provider presets
     */
    getEmailPresets(): Observable<{ [key: string]: EmailProviderPreset }> {
        return this.http.get<{ [key: string]: EmailProviderPreset }>(`${this.apiUrl}/email-config/presets`, { headers: this.authService.getAuthHeaders() });
    }

    /**
     * Get specific email provider preset
     */
    getEmailPreset(presetName: string): Observable<EmailProviderPreset> {
        return this.http.get<EmailProviderPreset>(`${this.apiUrl}/email-config/preset/${presetName}`, { headers: this.authService.getAuthHeaders() });
    }

    /**
     * Delete email configuration
     */
    deleteEmailConfig(): Observable<any> {
        return this.http.delete(`${this.apiUrl}/email-config`, { headers: this.authService.getAuthHeaders() });
    }

    /**
     * Migrate to external email provider
     */
    migrateToExternalProvider(providerType: string, config: any): Observable<any> {
        return this.http.post(`${this.apiUrl}/email-config/migrate`, {
            provider_type: providerType,
            ...config
        }, { headers: this.authService.getAuthHeaders() });
    }
}
