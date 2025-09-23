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
import { ConfirmationService } from 'primeng/api';

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
        ConfirmDialogModule
    ],
    templateUrl: './associations.component.html',
    styleUrls: ['./associations.component.scss'],
    providers: [ConfirmationService]
})
export class SuperadminAssociationsComponent implements OnInit {
    associations: Association[] = [];
    users: User[] = [];
    structures: Structure[] = [];
    loading = true;
    error: string | null = null;
    userFilter = '';
    structureFilter = '';
    showModal = false;
    associationFormData: any = {};

    userOptions: any[] = [];
    structureOptions: any[] = [];

    constructor(
        private superadminService: SuperadminService,
        private confirmationService: ConfirmationService
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
                this.error = error.message || 'Failed to load associations';
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
            this.error = 'User ID is required';
            return;
        }
        const userId = parseInt(userIdStr, 10);
        if (isNaN(userId)) {
            this.error = 'User ID must be a valid number';
            return;
        }

        // Validate structure_id
        const structureIdStr = this.associationFormData.structure_id?.toString().trim();
        if (!structureIdStr) {
            this.error = 'Structure ID is required';
            return;
        }
        const structureId = parseInt(structureIdStr, 10);
        if (isNaN(structureId)) {
            this.error = 'Structure ID must be a valid number';
            return;
        }

        this.superadminService.createAssociation(userId, structureId).subscribe({
            next: () => {
                this.closeModal();
                this.loadAssociations();
            },
            error: (error) => {
                this.error = error.message || 'Failed to create association';
            }
        });
    }

    deleteAssociation(association: Association): void {
        this.confirmationService.confirm({
            message: `Are you sure you want to remove ${association.user.name} from ${association.structure.name}?`,
            header: 'Confirm Removal',
            icon: 'pi pi-exclamation-triangle',
            accept: () => {
                this.superadminService.deleteAssociation(association.user_id, association.structure_id).subscribe({
                    next: () => {
                        this.loadAssociations();
                    },
                    error: (error) => {
                        this.error = error.message || 'Failed to delete association';
                    }
                });
            }
        });
    }
}
