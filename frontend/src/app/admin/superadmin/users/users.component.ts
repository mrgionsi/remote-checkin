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
    editingUser: User | null = null;
    userFormData: any = {};
    passwordFormData: any = {};
    roleOptions = [
        { label: 'All Roles', value: '' },
        { label: 'Admin', value: 'admin' },
        { label: 'Superadmin', value: 'superadmin' },
        { label: 'User', value: 'user' }
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
        // TODO: Implement association management
        this.showInfoMessage(`Manage associations for user: ${user.username}`);
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
