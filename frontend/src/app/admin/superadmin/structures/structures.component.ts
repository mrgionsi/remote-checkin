import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SuperadminService, Structure } from '../../../services/superadmin.service';

@Component({
    selector: 'app-superadmin-structures',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './structures.component.html',
    styleUrls: ['./structures.component.scss']
})
export class SuperadminStructuresComponent implements OnInit {
    structures: Structure[] = [];
    loading = true;
    error: string | null = null;
    searchTerm = '';
    statusFilter = '';
    pagination: any = null;
    showModal = false;
    editingStructure: Structure | null = null;
    structureFormData: any = {};

    constructor(private superadminService: SuperadminService) { }

    ngOnInit(): void {
        this.loadStructures();
    }

    loadStructures(): void {
        this.loading = true;
        this.error = null;

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
                this.error = error.message || 'Failed to load structures';
                this.loading = false;
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

    openCreateModal(): void {
        this.editingStructure = null;
        this.structureFormData = {
            name: '',
            city: '',
            street: '',
            cin: '',
            is_active: true
        };
        this.showModal = true;
    }

    editStructure(structure: Structure): void {
        this.editingStructure = structure;
        this.structureFormData = { ...structure };
        this.showModal = true;
    }

    closeModal(): void {
        this.showModal = false;
        this.editingStructure = null;
        this.structureFormData = {};
    }

    saveStructure(): void {
        if (this.editingStructure) {
            this.updateStructure();
        } else {
            this.createStructure();
        }
    }

    createStructure(): void {
        this.superadminService.createStructure(this.structureFormData).subscribe({
            next: () => {
                this.closeModal();
                this.loadStructures();
            },
            error: (error) => {
                this.error = error.message || 'Failed to create structure';
            }
        });
    }

    updateStructure(): void {
        if (!this.editingStructure) return;

        this.superadminService.updateStructure(this.editingStructure.id, this.structureFormData).subscribe({
            next: () => {
                this.closeModal();
                this.loadStructures();
            },
            error: (error) => {
                this.error = error.message || 'Failed to update structure';
            }
        });
    }

    toggleStructureStatus(structure: Structure): void {
        if (structure.is_active) {
            this.superadminService.deleteStructure(structure.id).subscribe({
                next: () => {
                    this.loadStructures();
                },
                error: (error) => {
                    this.error = error.message || 'Failed to archive structure';
                }
            });
        } else {
            this.superadminService.restoreStructure(structure.id).subscribe({
                next: () => {
                    this.loadStructures();
                },
                error: (error) => {
                    this.error = error.message || 'Failed to restore structure';
                }
            });
        }
    }
}
