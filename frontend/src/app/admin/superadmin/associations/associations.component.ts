import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SuperadminService, Association, Structure, User } from '../../../services/superadmin.service';

// PrimeNG imports
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { SelectModule } from 'primeng/select';
import { DialogModule } from 'primeng/dialog';
import { TagModule } from 'primeng/tag';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageModule } from 'primeng/message';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ToastModule } from 'primeng/toast';
import { TableModule } from 'primeng/table';
import { InputTextModule } from 'primeng/inputtext';
import { TooltipModule } from 'primeng/tooltip';
import { CheckboxModule } from 'primeng/checkbox';
import { ConfirmationService, MessageService } from 'primeng/api';

@Component({
    selector: 'app-superadmin-associations',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        ButtonModule,
        CardModule,
        SelectModule,
        DialogModule,
        TagModule,
        ProgressSpinnerModule,
        MessageModule,
        ConfirmDialogModule,
        ToastModule,
        TableModule,
        InputTextModule,
        TooltipModule,
        CheckboxModule
    ],
    templateUrl: './associations.component.html',
    styleUrls: ['./associations.component.scss'],
    providers: [ConfirmationService, MessageService]
})
export class SuperadminAssociationsComponent implements OnInit {
    associations: Association[] = [];
    users: User[] = [];
    structures: Structure[] = [];
    loading = true;
    submitting = false;
    error: string | null = null;
    userFilter = '';
    structureFilter = '';
    showModal = false;
    associationFormData: any = {};
    globalFilterValue = '';
    selectedAssociations: Association[] = [];
    selectAll = false;

    userOptions: any[] = [];
    structureOptions: any[] = [];

    constructor(
        private superadminService: SuperadminService,
        private confirmationService: ConfirmationService,
        private messageService: MessageService
    ) { }

    ngOnInit(): void {
        this.loadAssociations();
        this.loadUsers();
        this.loadStructures();
    }

    loadAssociations(): void {
        this.loading = true;
        this.error = null;

        const userId = this.userFilter ? parseInt(this.userFilter) : undefined;
        const structureId = this.structureFilter ? parseInt(this.structureFilter) : undefined;

        this.superadminService.getAssociations(userId, structureId).subscribe({
            next: (response) => {
                this.associations = response.associations;
                this.loading = false;
            },
            error: (error) => {
                this.handleError(error, 'Loading associations');
                this.loading = false;
            }
        });
    }

    loadUsers(): void {
        this.superadminService.getUsers({ per_page: 100 }).subscribe({
            next: (response) => {
                this.users = response.users;
                this.userOptions = [
                    { label: 'All Users', value: '' },
                    ...this.users.map(user => ({
                        label: `${user.name} ${user.surname} (${user.username})`,
                        value: user.id
                    }))
                ];
            },
            error: (error) => {
                console.error('Failed to load users:', error);
            }
        });
    }

    loadStructures(): void {
        this.superadminService.getStructures({ per_page: 100 }).subscribe({
            next: (response) => {
                this.structures = response.structures;
                this.structureOptions = [
                    { label: 'All Structures', value: '' },
                    ...this.structures.map(structure => ({
                        label: `${structure.name} (${structure.city})`,
                        value: structure.id
                    }))
                ];
            },
            error: (error) => {
                console.error('Failed to load structures:', error);
            }
        });
    }

    openCreateModal(): void {
        this.associationFormData = {
            user_id: '',
            structure_id: ''
        };
        this.showModal = true;
    }

    closeModal(): void {
        this.showModal = false;
        this.associationFormData = {};
    }

    createAssociation(): void {
        // Validate user_id
        const userIdStr = this.associationFormData.user_id?.toString().trim();
        if (!userIdStr) {
            this.showErrorMessage('User ID is required');
            return;
        }
        const userId = parseInt(userIdStr, 10);
        if (isNaN(userId)) {
            this.showErrorMessage('User ID must be a valid number');
            return;
        }

        // Validate structure_id
        const structureIdStr = this.associationFormData.structure_id?.toString().trim();
        if (!structureIdStr) {
            this.showErrorMessage('Structure ID is required');
            return;
        }
        const structureId = parseInt(structureIdStr, 10);
        if (isNaN(structureId)) {
            this.showErrorMessage('Structure ID must be a valid number');
            return;
        }

        this.submitting = true;
        this.superadminService.createAssociation(userId, structureId).subscribe({
            next: () => {
                this.submitting = false;
                this.closeModal();
                this.loadAssociations();
                this.showSuccessMessage('Association created successfully!');
            },
            error: (error) => {
                this.submitting = false;
                this.handleError(error, 'Creating association');
            }
        });
    }

    deleteAssociation(association: Association): void {
        this.confirmationService.confirm({
            message: `Are you sure you want to remove the association between ${association.user.name} ${association.user.surname} and ${association.structure.name}?`,
            header: 'Confirm Removal',
            icon: 'pi pi-exclamation-triangle',
            acceptButtonStyleClass: 'p-button-danger',
            rejectButtonStyleClass: 'p-button-secondary p-button-outlined',
            accept: () => {
                this.superadminService.deleteAssociation(association.user_id, association.structure_id).subscribe({
                    next: () => {
                        this.loadAssociations();
                        this.showSuccessMessage('Association removed successfully!');
                    },
                    error: (error) => {
                        this.handleError(error, 'Removing association');
                    }
                });
            }
        });
    }

    private showSuccessMessage(message: string): void {
        this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: message,
            life: 4000,
            closable: true
        });
    }

    private showErrorMessage(message: string): void {
        this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: message,
            life: 6000,
            closable: true
        });
    }

    private handleError(error: any, operation: string): void {
        console.error(`${operation} failed:`, error);

        let errorMessage = 'An unexpected error occurred. Please try again.';
        let hasBackendMessage = false;

        // Try to extract backend-provided error message
        if (error?.error?.message) {
            errorMessage = error.error.message;
            hasBackendMessage = true;
        } else if (error?.message) {
            errorMessage = error.message;
            hasBackendMessage = true;
        } else if (typeof error === 'string') {
            errorMessage = error;
            hasBackendMessage = true;
        }

        // Only apply generic status-based messages if no backend message was provided
        if (!hasBackendMessage && error?.status) {
            switch (error.status) {
                case 400:
                    errorMessage = 'Invalid request. Please check your input and try again.';
                    break;
                case 401:
                    errorMessage = 'You are not authorized to perform this action.';
                    break;
                case 403:
                    errorMessage = 'Access denied. You do not have permission to perform this action.';
                    break;
                case 404:
                    errorMessage = 'The requested resource was not found.';
                    break;
                case 409:
                    errorMessage = 'A conflict occurred. This association may already exist.';
                    break;
                case 422:
                    errorMessage = 'Validation error. Please check your input and try again.';
                    break;
                case 500:
                    errorMessage = 'Server error. Please try again later.';
                    break;
                case 503:
                    errorMessage = 'Service temporarily unavailable. Please try again later.';
                    break;
            }
        }

        this.showErrorMessage(`${operation}: ${errorMessage}`);
    }

    onGlobalFilter(event: any): void {
        this.globalFilterValue = event.target.value;
        // The table will automatically filter based on the globalFilterFields
    }

    onSelectAllChange(event: any): void {
        if (event.checked) {
            this.selectedAssociations = [...this.associations];
        } else {
            this.selectedAssociations = [];
        }
    }

    onSelectionChange(): void {
        this.selectAll = this.selectedAssociations.length === this.associations.length;
    }

    exportSelected(): void {
        if (this.selectedAssociations.length === 0) {
            this.showErrorMessage('Please select associations to export');
            return;
        }
        this.exportToCSV(this.selectedAssociations, 'selected-associations');
    }

    exportAll(): void {
        this.exportToCSV(this.associations, 'all-associations');
    }

    private exportToCSV(data: Association[], filename: string): void {
        const headers = ['User Name', 'Username', 'Structure Name', 'City', 'Status'];
        const csvContent = [
            headers.join(','),
            ...data.map(association => [
                `"${association.user.name} ${association.user.surname}"`,
                `"${association.user.username}"`,
                `"${association.structure.name}"`,
                `"${association.structure.city}"`,
                '"Active"'
            ].join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `${filename}-${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        this.showSuccessMessage(`${data.length} associations exported successfully!`);
    }

    deleteSelected(): void {
        if (this.selectedAssociations.length === 0) {
            this.showErrorMessage('Please select associations to delete');
            return;
        }

        this.confirmationService.confirm({
            message: `Are you sure you want to delete ${this.selectedAssociations.length} association(s)? This action cannot be undone.`,
            header: 'Confirm Bulk Delete',
            icon: 'pi pi-exclamation-triangle',
            acceptButtonStyleClass: 'p-button-danger',
            rejectButtonStyleClass: 'p-button-secondary p-button-outlined',
            accept: () => {
                this.performBulkDelete();
            }
        });
    }

    private performBulkDelete(): void {
        const deletePromises = this.selectedAssociations.map(association =>
            this.superadminService.deleteAssociation(association.user_id, association.structure_id).toPromise()
        );

        Promise.all(deletePromises)
            .then(() => {
                this.selectedAssociations = [];
                this.selectAll = false;
                this.loadAssociations();
                this.showSuccessMessage('Selected associations deleted successfully!');
            })
            .catch((error) => {
                this.handleError(error, 'Deleting selected associations');
            });
    }
}
