import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { SuperadminService, Structure } from '../../../services/superadmin.service';
import { ErrorHandlerService } from '../../../services/error-handler.service';
import { MessageService } from 'primeng/api';

// PrimeNG imports
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { DialogModule } from 'primeng/dialog';
import { CheckboxModule } from 'primeng/checkbox';
import { TagModule } from 'primeng/tag';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageModule } from 'primeng/message';
import { PaginatorModule } from 'primeng/paginator';
import { ToastModule } from 'primeng/toast';

@Component({
    selector: 'app-superadmin-structures',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        FormsModule,
        ButtonModule,
        CardModule,
        InputTextModule,
        SelectModule,
        DialogModule,
        CheckboxModule,
        TagModule,
        ProgressSpinnerModule,
        MessageModule,
        PaginatorModule,
        ToastModule
    ],
    providers: [MessageService],
    templateUrl: './structures.component.html',
    styleUrls: ['./structures.component.scss']
})
export class SuperadminStructuresComponent implements OnInit {
    structures: Structure[] = [];
    loading = true;
    searchTerm = '';
    statusFilter = '';
    pagination: any = null;
    showModal = false;
    editingStructure: Structure | null = null;
    structureForm!: FormGroup;
    submitting = false;

    statusOptions = [
        { label: 'All Status', value: '' },
        { label: 'Active', value: 'true' },
        { label: 'Archived', value: 'false' }
    ];

    constructor(
        private superadminService: SuperadminService,
        private fb: FormBuilder,
        private errorHandler: ErrorHandlerService,
        private messageService: MessageService
    ) { }

    ngOnInit(): void {
        this.initializeForm();
        this.loadStructures();
    }

    private initializeForm(): void {
        this.structureForm = this.fb.group({
            name: ['', [Validators.required]],
            city: ['', [Validators.required]],
            street: [''],
            cin: [''],
            is_active: [true]
        });
    }


    loadStructures(): void {
        this.loading = true;

        const params = {
            page: this.pagination?.page || 1,
            per_page: 10,
            search: this.searchTerm,
            is_active: this.statusFilter
        };

        this.superadminService.getStructures(params).subscribe({
            next: (response) => {
                this.structures = response.structures;
                this.pagination = response.pagination;
                this.loading = false;
            },
            error: (error) => {
                this.loading = false;
                this.showErrorMessage(this.errorHandler.getErrorMessageString(error));
            }
        });
    }

    onSearch(): void {
        // Debounce search
        setTimeout(() => {
            this.loadStructures();
        }, 300);
    }

    changePage(page: number): void {
        this.pagination.page = page;
        this.loadStructures();
    }

    onPageChange(event: any): void {
        // Guard against undefined event or missing properties
        if (!event || event.first === undefined || event.rows === undefined) {
            return;
        }

        // Ensure pagination object exists
        if (!this.pagination) {
            this.pagination = { page: 1 };
        }

        // Compute new page with safe arithmetic
        const newPage = Math.floor((event.first ?? 0) / (event.rows ?? 1)) + 1;
        this.pagination.page = newPage;

        this.loadStructures();
    }

    openCreateModal(): void {
        this.editingStructure = null;
        this.initializeForm();
        this.showModal = true;
    }

    editStructure(structure: Structure): void {
        this.editingStructure = structure;
        this.structureForm.patchValue({
            name: structure.name,
            city: structure.city,
            street: structure.street,
            cin: structure.cin,
            is_active: structure.is_active
        });
        this.showModal = true;
    }

    closeModal(): void {
        this.showModal = false;
        this.editingStructure = null;
        this.initializeForm();
    }

    saveStructure(): void {
        if (this.editingStructure) {
            this.updateStructure();
        } else {
            this.createStructure();
        }
    }

    createStructure(): void {
        if (this.structureForm.valid) {
            this.submitting = true;
            this.superadminService.createStructure(this.structureForm.value).subscribe({
                next: () => {
                    this.submitting = false;
                    this.closeModal();
                    this.loadStructures();
                    this.showSuccessMessage('Structure created successfully!');
                },
                error: (error) => {
                    this.submitting = false;
                    this.showErrorMessage(this.errorHandler.getErrorMessageString(error));
                }
            });
        } else {
            this.markFormGroupTouched();
        }
    }

    updateStructure(): void {
        if (!this.editingStructure) return;

        if (this.structureForm.valid) {
            this.submitting = true;
            this.superadminService.updateStructure(this.editingStructure.id, this.structureForm.value).subscribe({
                next: () => {
                    this.submitting = false;
                    this.closeModal();
                    this.loadStructures();
                    this.showSuccessMessage('Structure updated successfully!');
                },
                error: (error) => {
                    this.submitting = false;
                    this.showErrorMessage(this.errorHandler.getErrorMessageString(error));
                }
            });
        } else {
            this.markFormGroupTouched();
        }
    }

    private markFormGroupTouched(): void {
        Object.keys(this.structureForm.controls).forEach(key => {
            const control = this.structureForm.get(key);
            control?.markAsTouched();
        });
    }


    toggleStructureStatus(structure: Structure): void {
        if (structure.is_active) {
            this.superadminService.deleteStructure(structure.id).subscribe({
                next: () => {
                    this.loadStructures();
                    this.showSuccessMessage('Structure archived successfully!');
                },
                error: (error) => {
                    this.showErrorMessage(this.errorHandler.getErrorMessageString(error));
                }
            });
        } else {
            this.superadminService.restoreStructure(structure.id).subscribe({
                next: () => {
                    this.loadStructures();
                    this.showSuccessMessage('Structure restored successfully!');
                },
                error: (error) => {
                    this.showErrorMessage(this.errorHandler.getErrorMessageString(error));
                }
            });
        }
    }

    private showSuccessMessage(message: string): void {
        this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: message,
            life: 3000
        });
    }

    private showErrorMessage(message: string): void {
        this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: message,
            life: 5000
        });
    }
}
