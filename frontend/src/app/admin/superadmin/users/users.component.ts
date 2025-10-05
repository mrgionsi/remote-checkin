import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SuperadminService, User } from '../../../services/superadmin.service';
import { ErrorHandlerService } from '../../../services/error-handler.service';
import { MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { MessageModule } from 'primeng/message';
import { PaginatorModule, PaginatorState } from 'primeng/paginator';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { SelectModule } from 'primeng/select';
import { InputTextModule } from 'primeng/inputtext';
import { DialogModule } from 'primeng/dialog';
import { ToastModule } from 'primeng/toast';

@Component({
    selector: 'app-superadmin-users',
    standalone: true,
    imports: [CommonModule, FormsModule, ButtonModule, CardModule, TagModule, MessageModule, PaginatorModule, ProgressSpinnerModule, SelectModule, InputTextModule, DialogModule, ToastModule],
    providers: [MessageService],
    templateUrl: './users.component.html',
    styleUrls: ['./users.component.scss']
})
export class SuperadminUsersComponent implements OnInit {
    onPageChange(event: PaginatorState): void {
        // Guard against undefined event or missing properties
        if (!event?.first || !event?.rows) {
            return;
        }

        // Ensure pagination object exists
        if (!this.pagination) {
            this.pagination = { page: 1 };
        }

        // Compute new page with safe arithmetic
        const newPage = Math.floor((event.first ?? 0) / (event.rows ?? 1)) + 1;
        this.pagination.page = newPage;

        this.loadUsers();
    }
    users: User[] = [];
    loading = true;
    submitting = false;
    error: string | null = null;
    searchTerm = '';
    roleFilter = '';
    pagination: any = null;
    showModal = false;
    showPasswordModal = false;
    showStructuresModal = false;
    editingUser: User | null = null;
    selectedUser: User | null = null;
    userFormData: any = {};
    passwordFormData: any = {};
    userStructures: Array<{ id: number; name: string; city: string }> = [];
    availableStructures: Array<{ id: number; name: string; city: string }> = [];
    selectedStructureId: number | null = null;

    // Role change properties
    showRoleModal: boolean = false;
    availableRoles: any[] = [];
    selectedRoleId: number | null = null;
    roleOptions = [
        { label: 'All Roles', value: '' },
        { label: 'Administrator', value: 'administrator' },
        { label: 'Superadmin', value: 'superadmin' },
    ];

    constructor(
        private superadminService: SuperadminService,
        private errorHandler: ErrorHandlerService,
        private messageService: MessageService
    ) { }

    ngOnInit(): void {
        this.loadUsers();
    }

    loadUsers(): void {
        this.loading = true;
        this.error = null;

        const params = {
            page: this.pagination?.page || 1,
            per_page: 10,
            search: this.searchTerm,
            role: this.roleFilter
        };

        this.superadminService.getUsers(params).subscribe({
            next: (response) => {
                this.users = response.users;
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
            this.loadUsers();
        }, 300);
    }

    changePage(page: number): void {
        this.pagination.page = page;
        this.loadUsers();
    }

    openCreateModal(): void {
        this.editingUser = null;
        this.userFormData = {
            username: '',
            password: '',
            name: '',
            surname: '',
            email: '',
            telephone: ''
            // id_role omitted - backend will default to administrator role
        };
        this.showModal = true;
    }

    editUser(user: User): void {
        this.editingUser = user;
        this.userFormData = { ...user };
        this.showModal = true;
    }

    closeModal(): void {
        this.showModal = false;
        this.editingUser = null;
        this.userFormData = {};
    }

    saveUser(): void {
        if (this.editingUser) {
            this.updateUser();
        } else {
            this.createUser();
        }
    }

    createUser(): void {
        this.submitting = true;
        this.superadminService.createUser(this.userFormData).subscribe({
            next: () => {
                this.submitting = false;
                this.closeModal();
                this.loadUsers();
                this.showSuccessMessage('User created successfully!');
            },
            error: (error) => {
                this.submitting = false;
                this.showErrorMessage(this.errorHandler.getErrorMessageString(error));
            }
        });
    }

    updateUser(): void {
        if (!this.editingUser) return;

        this.submitting = true;
        this.superadminService.updateUser(this.editingUser.id, this.userFormData).subscribe({
            next: () => {
                this.submitting = false;
                this.closeModal();
                this.loadUsers();
                this.showSuccessMessage('User updated successfully!');
            },
            error: (error) => {
                this.submitting = false;
                this.showErrorMessage(this.errorHandler.getErrorMessageString(error));
            }
        });
    }

    resetPassword(user: User): void {
        this.editingUser = user;
        this.passwordFormData = { password: '' };
        this.showPasswordModal = true;
    }

    closePasswordModal(): void {
        this.showPasswordModal = false;
        this.editingUser = null;
        this.passwordFormData = {};
    }

    confirmResetPassword(): void {
        if (!this.editingUser) return;

        this.submitting = true;
        this.superadminService.resetUserPassword(this.editingUser.id, this.passwordFormData.password).subscribe({
            next: () => {
                this.submitting = false;
                this.closePasswordModal();
                this.showSuccessMessage('Password reset successfully!');
            },
            error: (error) => {
                this.submitting = false;
                this.showErrorMessage(this.errorHandler.getErrorMessageString(error));
            }
        });
    }

    manageAssociations(user: User): void {
        this.selectedUser = user;
        this.userStructures = (user.structures || []).map(s => ({ ...s, city: '' }));
        this.selectedStructureId = null;
        this.loadAvailableStructures();
        this.showStructuresModal = true;
    }

    closeStructuresModal(): void {
        this.showStructuresModal = false;
        this.selectedUser = null;
        this.userStructures = [];
        this.availableStructures = [];
        this.selectedStructureId = null;
    }

    loadAvailableStructures(): void {
        this.superadminService.getStructures({ per_page: 1000 }).subscribe({
            next: (response) => {
                const allStructures = response.structures || [];
                const userStructureIds = this.userStructures.map(s => s.id);
                this.availableStructures = allStructures
                    .filter((structure: any) => !userStructureIds.includes(structure.id))
                    .map((structure: any) => ({
                        id: structure.id,
                        name: structure.name,
                        city: structure.city
                    }));
            },
            error: (error) => {
                this.showErrorMessage(this.errorHandler.getErrorMessageString(error));
            }
        });
    }

    addStructureToUser(): void {
        if (!this.selectedUser || !this.selectedStructureId) return;

        this.submitting = true;
        this.superadminService.createAssociation(this.selectedUser.id, this.selectedStructureId).subscribe({
            next: () => {
                this.submitting = false;
                this.closeStructuresModal();
                this.loadAvailableStructures();
                this.loadUsers(); // Refresh the user list
                this.selectedStructureId = null;
                this.showSuccessMessage('Structure assigned successfully!');
            },
            error: (error) => {
                this.submitting = false;
                this.showErrorMessage(this.errorHandler.getErrorMessageString(error));
            }
        });
    }

    removeStructureFromUser(structureId: number): void {
        if (!this.selectedUser) return;

        this.submitting = true;
        this.superadminService.deleteAssociation(this.selectedUser.id, structureId).subscribe({
            next: () => {
                this.submitting = false;
                this.showSuccessMessage('Structure removed successfully!');
                this.loadAvailableStructures();
                this.loadUsers(); // Refresh the user list
            },
            error: (error) => {
                this.submitting = false;
                this.showErrorMessage(this.errorHandler.getErrorMessageString(error));
            }
        });
    }

    // Role Management Methods
    openRoleChangeModal(user: User): void {
        this.selectedUser = user;
        this.selectedRoleId = user.id_role;
        this.loadAvailableRoles();
        this.showRoleModal = true;
    }

    closeRoleModal(): void {
        this.showRoleModal = false;
        this.selectedUser = null;
        this.selectedRoleId = null;
        this.availableRoles = [];
    }

    loadAvailableRoles(): void {
        this.superadminService.getRoles().subscribe({
            next: (response) => {
                // Filter to only show administrator and superadmin roles
                this.availableRoles = response.roles.filter((role: any) =>
                    role.name === 'administrator' || role.name === 'superadmin'
                );
            },
            error: (error) => {
                this.showErrorMessage(this.errorHandler.getErrorMessageString(error));
            }
        });
    }

    confirmRoleChange(): void {
        if (!this.selectedUser || !this.selectedRoleId) return;

        this.submitting = true;
        this.superadminService.changeUserRole(this.selectedUser.id, this.selectedRoleId).subscribe({
            next: () => {
                this.submitting = false;
                this.closeRoleModal();
                this.loadUsers(); // Refresh the user list
                this.showSuccessMessage('User role changed successfully!');
            },
            error: (error) => {
                this.submitting = false;
                this.showErrorMessage(this.errorHandler.getErrorMessageString(error));
            }
        });
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

    private showInfoMessage(message: string): void {
        this.messageService.add({
            severity: 'info',
            summary: 'Info',
            detail: message,
            life: 3000
        });
    }
}
