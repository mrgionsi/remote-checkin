import { CommonModule } from '@angular/common';
import { Component, Inject, Optional } from '@angular/core';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { DialogModule } from 'primeng/dialog';
import { DynamicDialogRef, DynamicDialogConfig } from 'primeng/dynamicdialog';
import { ImageModule } from 'primeng/image';
import { DocumentTypeLabelPipe } from "../pipes/document-type-label.pipe";
import { TranslocoPipe } from '@jsverse/transloco';
import { TooltipModule } from 'primeng/tooltip';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-person-detail-dialog',
  imports: [DialogModule, CommonModule, ImageModule, ButtonModule, CardModule, TranslocoPipe, TooltipModule],
  templateUrl: './person-detail-dialog.component.html',
  styleUrls: ['./person-detail-dialog.component.scss'],
  standalone: true
})
export class PersonDetailDialogComponent {
  person: any;
  display: boolean = true;  // Controls the visibility of the main dialog
  fullscreenVisible: boolean = false; // Controls the visibility of fullscreen image
  fullscreenImage: string | null = null;  // Holds the clicked image URL

  // Mapping data for display
  countryMappings: { [key: string]: string } = {};
  municipalityMappings: { [key: string]: string } = {};
  documentTypeMappings: { [key: string]: string } = {};

  constructor(public ref: DynamicDialogRef, @Inject(DynamicDialogConfig) public data: any, @Optional() private http: HttpClient) {
    this.person = data.data.person;
    this.loadReferenceData();
  }
  viewImage(imageUrl: string) {
    this.fullscreenImage = imageUrl; // Set the clicked image URL
    this.fullscreenVisible = true;  // Open the fullscreen dialog
  }

  // Load reference data from JSON files
  private loadReferenceData() {
    if (!this.http) {
      // Fallback to static data if HttpClient is not available
      this.initializeFallbackData();
      return;
    }

    Promise.all([
      this.loadCountries(),
      this.loadMunicipalities(),
      this.loadDocumentTypes()
    ]).catch(error => {
      console.error('Error loading reference data:', error);
      this.initializeFallbackData();
    });
  }

  private async loadCountries(): Promise<void> {
    try {
      const countries = await this.http!.get<{ [key: string]: string }>('/assets/data/countries.json').toPromise();
      if (countries) {
        this.countryMappings = countries;
      }
    } catch (error) {
      console.error('Error loading countries:', error);
      this.initializeFallbackCountries();
    }
  }

  private async loadMunicipalities(): Promise<void> {
    try {
      const municipalities = await this.http!.get<{ [key: string]: string }>('/assets/data/municipalities.json').toPromise();
      if (municipalities) {
        this.municipalityMappings = municipalities;
      }
    } catch (error) {
      console.error('Error loading municipalities:', error);
      this.initializeFallbackMunicipalities();
    }
  }

  private async loadDocumentTypes(): Promise<void> {
    try {
      const documentTypes = await this.http!.get<{ [key: string]: string }>('/assets/data/document_types.json').toPromise();
      if (documentTypes) {
        this.documentTypeMappings = documentTypes;
      }
    } catch (error) {
      console.error('Error loading document types:', error);
      this.initializeFallbackDocumentTypes();
    }
  }

  private initializeFallbackData() {
    this.initializeFallbackCountries();
    this.initializeFallbackMunicipalities();
    this.initializeFallbackDocumentTypes();
  }

  private initializeFallbackCountries() {
    this.countryMappings = {
      '100000100': 'ITALIA',
      '100000536': 'STATI UNITI D\'AMERICA',
      '100000219': 'REGNO UNITO',
      '100000215': 'FRANCIA'
    };
  }

  private initializeFallbackMunicipalities() {
    this.municipalityMappings = {
      '058091': 'ROMA',
      '015146': 'MILANO',
      '063049': 'NAPOLI',
      '001272': 'TORINO'
    };
  }

  private initializeFallbackDocumentTypes() {
    this.documentTypeMappings = {
      'IDENT': 'CARTA DI IDENTITA\'',
      'PASOR': 'PASSAPORTO ORDINARIO',
      'PATEN': 'PATENTE DI GUIDA',
      'IDELE': 'CARTA IDENTITA\' ELETTRONICA'
    };
  }

  // Helper method to get country display name by code
  getCountryDisplayName(code: string): string {
    return this.countryMappings[code] || code || '-';
  }

  // Helper method to get municipality display name by code
  getMunicipalityDisplayName(code: string): string {
    return this.municipalityMappings[code] || code || '-';
  }

  // Helper method to get document type display name by code
  getDocumentTypeDisplayName(code: string): string {
    return this.documentTypeMappings[code] || code || '-';
  }

  // Open Image in a New Tab
  openInNewTab(imageUrl: string) {
    window.open(imageUrl, '_blank');
  }

  forceDownload(imageUrl: string) {
    fetch(imageUrl)
      .then(response => {
        // Get the filename from the Content-Disposition header if available
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'download.jpg'; // Default filename

        if (contentDisposition) {
          const match = contentDisposition.match(/filename="?([^"]+)"?/);
          if (match && match[1]) {
            filename = match[1];
          }
        } else {
          // Extract filename from the URL if Content-Disposition is missing
          const urlParts = imageUrl.split('/');
          filename = urlParts[urlParts.length - 1];
        }

        return response.blob().then(blob => ({ blob, filename }));
      })
      .then(({ blob, filename }) => {
        const blobUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(blobUrl);
      })
      .catch(error => console.error('Download failed:', error));
  }


}
