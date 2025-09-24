import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SuperadminService, User } from '../../../services/superadmin.service';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { MessageModule } from 'primeng/message';
import { PaginatorModule } from 'primeng/paginator';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { PaginatorState } from 'primeng/paginator';
import { SelectModule } from 'primeng/select';
import { InputTextModule } from 'primeng/inputtext';

@Component({
    selector: 'app-superadmin-users',
    standalone: true,
    imports: [CommonModule, FormsModule, ButtonModule, CardModule, TagModule, MessageModule, PaginatorModule, ProgressSpinnerModule, SelectModule, InputTextModule],
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
    error: string | null = null;
    searchTerm = '';
    roleFilter = '';
    pagination: any = null;
    showModal = false;
    showPasswordModal = false;
    editingUser: User | null = null;
    userFormData: any = {};
    passwordFormData: any = {};
    roleOptions: any;

    constructor(private superadminService: SuperadminService) { }

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
                this.error = error.message || 'Failed to load users';
                this.loading = false;
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
        this.superadminService.createUser(this.userFormData).subscribe({
            next: () => {
                this.closeModal();
                this.loadUsers();
            },
            error: (error) => {
                this.error = error.message || 'Failed to create user';
            }
        });
    }

    updateUser(): void {
        if (!this.editingUser) return;

        this.superadminService.updateUser(this.editingUser.id, this.userFormData).subscribe({
            next: () => {
                this.closeModal();
                this.loadUsers();
            },
            error: (error) => {
                this.error = error.message || 'Failed to update user';
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

        this.superadminService.resetUserPassword(this.editingUser.id, this.passwordFormData.password).subscribe({
            next: () => {
                this.closePasswordModal();
                // Show success message
                alert('Password reset successfully');
            },
            error: (error) => {
                this.error = error.message || 'Failed to reset password';
            }
        });
    }

    manageAssociations(user: User): void {
        // TODO: Implement association management
        alert(`Manage associations for user: ${user.username}`);
    }
}
