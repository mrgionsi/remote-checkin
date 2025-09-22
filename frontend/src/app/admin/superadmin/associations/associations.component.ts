import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SuperadminService, Association, Structure, User } from '../../../services/superadmin.service';

@Component({
  selector: 'app-superadmin-associations',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './associations.component.html',
  styleUrls: ['./associations.component.scss']
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

  constructor(private superadminService: SuperadminService) { }

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
    const userId = parseInt(this.associationFormData.user_id);
    const structureId = parseInt(this.associationFormData.structure_id);
    
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
    if (confirm(`Are you sure you want to remove ${association.user.name} from ${association.structure.name}?`)) {
      this.superadminService.deleteAssociation(association.user_id, association.structure_id).subscribe({
        next: () => {
          this.loadAssociations();
        },
        error: (error) => {
          this.error = error.message || 'Failed to delete association';
        }
      });
    }
  }
}
