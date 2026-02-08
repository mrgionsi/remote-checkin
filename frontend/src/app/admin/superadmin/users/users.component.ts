import { Component, OnInit, OnDestroy, HostListener } from '@angular/core';
import { Subscription } from 'rxjs';
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
export class SuperadminUsersComponent implements OnInit, OnDestroy {
    private componentId = Math.random().toString(36).substr(2, 9); // Unique component ID

    onPageChange(event: PaginatorState): void {
        // Guard against undefined event or missing properties
        if (event?.first === undefined || event?.first === null || event?.rows === undefined || event?.rows === null) {
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

    // Subscription management
    private subscriptions: Subscription[] = [];
    private isLoadingUsers = false; // Prevent duplicate API calls
    private static globalUsersLoading = false; // Global flag to prevent multiple API calls

    // Loading states for individual operations
    loadingStructures = false;
    loadingRoles = false;
    submittingPassword = false;
    submittingStructure = false;
    submittingRole = false;

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

    ngOnDestroy(): void {
        // Clean up all subscriptions to prevent memory leaks
        this.subscriptions.forEach(sub => {
            if (sub && !sub.closed) {
                sub.unsubscribe();
            }
        });
        this.subscriptions = [];

        // Reset global loading flag when component is destroyed
        SuperadminUsersComponent.globalUsersLoading = false;
    }

    trackByUserId(index: number, user: User): number {
        return user.id;
    }

    @HostListener('document:keydown.escape', ['$event'])
    onEscapeKey(event: KeyboardEvent): void {
        // Close any open dialog when ESC is pressed
        if (this.showModal) {
            this.closeModal();
        } else if (this.showPasswordModal) {
            this.closePasswordModal();
        } else if (this.showStructuresModal) {
            this.closeStructuresModal();
        } else if (this.showRoleModal) {
            this.closeRoleModal();
        }
    }

    loadUsers(): void {
        // Prevent duplicate API calls globally
        if (SuperadminUsersComponent.globalUsersLoading) {
            // Reset loading state since we're not making a new request
            this.loading = false;
            return;
        }

        SuperadminUsersComponent.globalUsersLoading = true;
        this.isLoadingUsers = true;
        this.loading = true;
        this.error = null;

        const params = {
            page: this.pagination?.page || 1,
            per_page: 10,
            search: this.searchTerm,
            role: this.roleFilter
        };

        const subscription = this.superadminService.getUsers(params).subscribe({
            next: (response) => {
                this.users = response.users || [];
                this.pagination = response.pagination;
                this.loading = false;
                this.isLoadingUsers = false;
                SuperadminUsersComponent.globalUsersLoading = false;
            },
            error: (error) => {
                this.loading = false;
                this.isLoadingUsers = false;
                SuperadminUsersComponent.globalUsersLoading = false;
                this.handleError(error, 'Loading users');
            }
        });

        this.subscriptions.push(subscription);
    }

    setRoleFilter(role: string): void {
        this.roleFilter = role;
        this.loadUsers();
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
        if (this.validateUserForm()) {
            if (this.editingUser) {
                this.updateUser();
            } else {
                this.createUser();
            }
        }
    }

    private validateUserForm(): boolean {
        if (!this.userFormData.username?.trim()) {
            this.showErrorMessage('Username is required');
            return false;
        }

        if (!this.editingUser && !this.userFormData.password?.trim()) {
            this.showErrorMessage('Password is required for new users');
            return false;
        }

        if (!this.userFormData.name?.trim()) {
            this.showErrorMessage('First name is required');
            return false;
        }

        if (!this.userFormData.surname?.trim()) {
            this.showErrorMessage('Last name is required');
            return false;
        }

        // Email validation if provided
        if (this.userFormData.email && !this.isValidEmail(this.userFormData.email)) {
            this.showErrorMessage('Please enter a valid email address');
            return false;
        }

        // Password strength validation for new users
        if (!this.editingUser && this.userFormData.password && !this.isValidPassword(this.userFormData.password)) {
            this.showErrorMessage('Password must be at least 8 characters long and contain at least one letter and one number');
            return false;
        }

        return true;
    }

    private isValidEmail(email: string): boolean {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    private isValidPassword(password: string): boolean {
        // At least 8 characters, one letter, one number
        const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$/;
        return passwordRegex.test(password);
    }

    createUser(): void {
        this.submitting = true;
        const subscription = this.superadminService.createUser(this.userFormData).subscribe({
            next: () => {
                this.submitting = false;
                this.closeModal();
                this.loadUsers();
                this.showSuccessMessage('User created successfully!');
            },
            error: (error) => {
                this.submitting = false;
                this.handleError(error, 'Creating user');
            }
        });

        this.subscriptions.push(subscription);
    }

    updateUser(): void {
        if (!this.editingUser) return;

        this.submitting = true;
        const subscription = this.superadminService.updateUser(this.editingUser.id, this.userFormData).subscribe({
            next: () => {
                this.submitting = false;
                this.closeModal();
                this.loadUsers();
                this.showSuccessMessage('User updated successfully!');
            },
            error: (error) => {
                this.submitting = false;
                this.handleError(error, 'Updating user');
            }
        });

        this.subscriptions.push(subscription);
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

        if (!this.validatePasswordForm()) {
            return;
        }

        this.submittingPassword = true;
        const subscription = this.superadminService.resetUserPassword(this.editingUser.id, this.passwordFormData.password).subscribe({
            next: () => {
                this.submittingPassword = false;
                this.closePasswordModal();
                this.showSuccessMessage('Password reset successfully!');
            },
            error: (error) => {
                this.submittingPassword = false;
                this.handleError(error, 'Resetting password');
            }
        });

        this.subscriptions.push(subscription);
    }

    private validatePasswordForm(): boolean {
        if (!this.passwordFormData.password?.trim()) {
            this.showErrorMessage('New password is required');
            return false;
        }

        if (!this.isValidPassword(this.passwordFormData.password)) {
            this.showErrorMessage('Password must be at least 8 characters long and contain at least one letter and one number');
            return false;
        }

        return true;
    }

    manageAssociations(user: User): void {
        this.selectedUser = user;
        this.userStructures = (user.structures || []).map(s => ({ ...s, city: (s as any).city || '' }));
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
        this.loadingStructures = true;
        const subscription = this.superadminService.getStructures({ per_page: 1000 }).subscribe({
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
                this.loadingStructures = false;
            },
            error: (error) => {
                this.loadingStructures = false;
                this.handleError(error, 'Loading structures');
            }
        });

        this.subscriptions.push(subscription);
    }

    addStructureToUser(): void {
        if (!this.selectedUser || !this.selectedStructureId) return;

        this.submittingStructure = true;
        const subscription = this.superadminService.createAssociation(this.selectedUser.id, this.selectedStructureId).subscribe({
            next: () => {
                this.submittingStructure = false;
                this.closeStructuresModal();
                this.loadAvailableStructures();
                this.loadUsers(); // Refresh the user list
                this.selectedStructureId = null;
                this.showSuccessMessage('Structure assigned successfully!');
            },
            error: (error) => {
                this.submittingStructure = false;
                this.handleError(error, 'Adding structure');
            }
        });

        this.subscriptions.push(subscription);
    }

    removeStructureFromUser(structureId: number): void {
        if (!this.selectedUser) return;

        this.submittingStructure = true;
        const subscription = this.superadminService.deleteAssociation(this.selectedUser.id, structureId).subscribe({
            next: () => {
                this.submittingStructure = false;
                // Keep local lists in sync before reloading
                this.userStructures = this.userStructures.filter(s => s.id !== structureId);
                if (this.selectedUser) {
                    this.selectedUser.structures = (this.selectedUser.structures || []).filter(s => s.id !== structureId);
                }
                this.showSuccessMessage('Structure removed successfully!');
                this.loadAvailableStructures();
                this.loadUsers(); // Refresh the user list
            },
            error: (error) => {
                this.submittingStructure = false;
                this.handleError(error, 'Removing structure');
            }
        });

        this.subscriptions.push(subscription);
    }

    // Role Management Methods
    openRoleChangeModal(user: User): void {
        this.selectedUser = user;
        // Initialize with null - will be set after roles are loaded
        this.selectedRoleId = null;
        this.loadAvailableRoles();
        // Don't show modal here - it will be shown after roles are loaded
    }

    closeRoleModal(): void {
        this.showRoleModal = false;
        this.selectedUser = null;
        this.selectedRoleId = null;
        this.availableRoles = [];
    }

    loadAvailableRoles(): void {
        this.loadingRoles = true;
        const subscription = this.superadminService.getRoles().subscribe({
            next: (response) => {
                // Filter to only show administrator and superadmin roles
                this.availableRoles = response.roles.filter((role: any) =>
                    role.name === 'administrator' || role.name === 'superadmin'
                );

                // Initialize selectedRoleId to the user's current role
                // This ensures the "Change Role" button is disabled until a different role is selected
                this.selectedRoleId = this.getCurrentRoleId();

                this.loadingRoles = false;

                // Show modal only after roles are loaded and selectedRoleId is properly initialized
                // This prevents the race condition where the button appears enabled incorrectly
                this.showRoleModal = true;
            },
            error: (error) => {
                this.loadingRoles = false;
                this.handleError(error, 'Loading roles');
            }
        });

        this.subscriptions.push(subscription);
    }

    getCurrentRoleId(): number | null {
        // Get the current role ID based on the user's role name
        // This is more reliable than using id_role which may contain incorrect data
        if (!this.selectedUser || !this.selectedUser.role || !this.availableRoles.length) {
            return null;
        }

        const currentRole = this.availableRoles.find((role: any) =>
            role.name === this.selectedUser?.role
        );

        return currentRole ? currentRole.id : null;
    }

    confirmRoleChange(): void {
        if (!this.selectedUser || !this.selectedRoleId) return;

        this.submittingRole = true;
        const subscription = this.superadminService.changeUserRole(this.selectedUser.id, this.selectedRoleId).subscribe({
            next: () => {
                this.submittingRole = false;
                this.closeRoleModal();
                this.loadUsers(); // Refresh the user list
                this.showSuccessMessage('User role changed successfully!');
            },
            error: (error) => {
                this.submittingRole = false;
                this.handleError(error, 'Changing role');
            }
        });

        this.subscriptions.push(subscription);
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

    private showInfoMessage(message: string): void {
        this.messageService.add({
            severity: 'info',
            summary: 'Info',
            detail: message,
            life: 4000,
            closable: true
        });
    }

    private showWarningMessage(message: string): void {
        this.messageService.add({
            severity: 'warn',
            summary: 'Warning',
            detail: message,
            life: 4000,
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
                    errorMessage = 'A conflict occurred. The resource may already exist or be in use.';
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
}
