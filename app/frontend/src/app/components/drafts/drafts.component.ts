import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ProjectItem, ProjectsService } from '../../services/projects.service';

@Component({
  selector: 'app-drafts',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './drafts.component.html',
  styleUrls: ['./drafts.component.css']
})
export class DraftsComponent {
  drafts: ProjectItem[] = [];
  showPreview = false;
  previewMarkdown = '';
  isEditing = false;
  editContent = '';
  currentDraft: ProjectItem | null = null;
  sortOrder: 'dateDesc' | 'dateAsc' | 'alphabetical' = 'dateDesc';

  constructor(
    private draftsService: ProjectsService,
  ) {
    this.load();
  }

  load(): void {
    this.drafts = this.draftsService.getAll();
    this.sortDrafts();
  }

  deleteDraft(id: string): void {
    this.load();
  }

  openPreviewMarkdown(draft: ProjectItem): void {
    // Get fresh draft data from service to ensure we have the latest markdown
    const freshDraft = this.draftsService.getById(draft.id);
    if (!freshDraft) return;

    const created = new Date(freshDraft.createdAt).toLocaleString();
    const updated = new Date(freshDraft.updatedAt).toLocaleString();
    const kw = freshDraft.keywords && freshDraft.keywords.length ? `\n\n**Keywords:** ${freshDraft.keywords.join(', ')}` : '';

    // Use saved markdown if available, otherwise generate default
    if (freshDraft.markdown) {
      this.previewMarkdown = freshDraft.markdown;
    } else {
      this.previewMarkdown = `# ${freshDraft.title}\n\nCreated: ${created}\n\nUpdated: ${updated}${kw}`;
    }

    this.editContent = this.previewMarkdown;
    this.isEditing = false;
    this.showPreview = true;
  }

  closePreview(): void {
    this.showPreview = false;
    this.previewMarkdown = '';
    this.isEditing = false;
    this.editContent = '';
    this.currentDraft = null;
  }

  toggleEdit(): void {
    this.isEditing = !this.isEditing;
    if (this.isEditing) {
      this.editContent = this.previewMarkdown;
    }
  }

  saveEdit(): void {
    if (!this.currentDraft) return;
    this.previewMarkdown = this.editContent;
    this.isEditing = false;
    // Save the markdown content to localStorage
    // Reload drafts to get updated data
    this.load();
  }

  cancelEdit(): void {
    this.editContent = this.previewMarkdown;
    this.isEditing = false;
  }

  sortDrafts(): void {
    switch (this.sortOrder) {
      case 'dateDesc':
        this.drafts.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
        break;
      case 'dateAsc':
        this.drafts.sort((a, b) => new Date(a.updatedAt).getTime() - new Date(b.updatedAt).getTime());
        break;
      case 'alphabetical':
        this.drafts.sort((a, b) => a.title.localeCompare(b.title));
        break;
    }
  }

  onSortChange(): void {
    this.sortDrafts();
  }
}


