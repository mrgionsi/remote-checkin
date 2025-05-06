import { CommonModule } from '@angular/common';
import { Component, Inject } from '@angular/core';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { DialogModule } from 'primeng/dialog';
import { DynamicDialogRef, DynamicDialogConfig } from 'primeng/dynamicdialog';
import { ImageModule } from 'primeng/image';
import { DocumentTypeLabelPipe } from "../pipes/document-type-label.pipe";

@Component({
  selector: 'app-person-detail-dialog',
  imports: [DialogModule, CommonModule, ImageModule, ButtonModule, CardModule, DocumentTypeLabelPipe],
  templateUrl: './person-detail-dialog.component.html',
  styleUrl: './person-detail-dialog.component.scss'
})
export class PersonDetailDialogComponent {
  person: any;
  display: boolean = true;  // Controls the visibility of the main dialog
  fullscreenVisible: boolean = false; // Controls the visibility of fullscreen image
  fullscreenImage: string | null = null;  // Holds the clicked image URL

  constructor(public ref: DynamicDialogRef, @Inject(DynamicDialogConfig) public data: any) {
    console.log(data.data.person)
    this.person = data.data.person;
  }
  viewImage(imageUrl: string) {
    this.fullscreenImage = imageUrl; // Set the clicked image URL
    this.fullscreenVisible = true;  // Open the fullscreen dialog
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
