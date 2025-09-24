import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ProjectItem, ProjectsService } from '../../services/projects.service';
import { RequestStatus } from '../../types/models';
import { marked } from 'marked';

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
  previewMarkdown: String | null = null;
  currentDraft: ProjectItem | null = null;
  sortOrder: 'dateDesc' | 'dateAsc' | 'alphabetical' = 'dateDesc';

  constructor(
    private projectsService: ProjectsService,
  ) {
    this.load();
  }

  load(): void {
    this.drafts = this.projectsService.getAll();
    this.sortDrafts();
  }

  deleteDraft(id: string): void {
    this.projectsService.delete(id);
    this.load();
  }

  openPreviewMarkdown(draft: ProjectItem): void {
    // Get fresh draft data from service to ensure we have the latest markdown
    const freshProject = this.projectsService.getById(draft.id);
    if (!freshProject) return;

    // const created = new Date(freshProject.createdAt).toLocaleString();
    // const updated = new Date(freshProject.updatedAt).toLocaleString();
    // const kw = freshProject.keywords && freshProject.keywords.length ? `\n\n**Keywords:** ${freshProject.keywords.join(', ')}` : '';

    // Use saved markdown if available, otherwise generate default
    // if (freshProject.markdown) {
    //   this.previewMarkdown = freshProject.markdown;
    // } else {
      // this.previewMarkdown = `# ${freshProject.title}\n\nCreated: ${created}\n\nUpdated: ${updated}${kw}`;
      this.updateDraftMarkdown(freshProject.requestStatus);
    // }

    this.showPreview = true;
  }

  closePreview(): void {
    this.showPreview = false;
    this.previewMarkdown = null;
    this.currentDraft = null;
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

  private updateDraftMarkdown(rs: RequestStatus): void {
    try {
      if (!rs || !Array.isArray(rs.draft)) {
        this.previewMarkdown = null;
        return;
      }
      const md = rs.draft
        .map(h => `${h.title}\n\n${h.content ?? ''}`) // The title already has a leading #
        .join('\n\n');
      const html = marked.parse(md);
      this.previewMarkdown = String(html);
    } catch {
      this.previewMarkdown = null;
    }
  }
}


