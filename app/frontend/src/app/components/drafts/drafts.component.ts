import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { DraftItem, DraftsService } from '../../services/drafts.service';

@Component({
  selector: 'app-drafts',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './drafts.component.html',
  styleUrls: ['./drafts.component.css']
})
export class DraftsComponent {
  drafts: DraftItem[] = [];
  showPreview = false;
  previewMarkdown = '';

  constructor(private draftsService: DraftsService) {
    this.load();
  }

  load(): void {
    this.drafts = this.draftsService.getAll();
  }

  deleteDraft(id: string): void {
    this.draftsService.delete(id);
    this.load();
  }

  openPreviewMarkdown(draft: DraftItem): void {
    if (draft.status !== 'ready') return;
    const created = new Date(draft.createdAt).toLocaleString();
    const updated = new Date(draft.updatedAt).toLocaleString();
    const kw = draft.keywords && draft.keywords.length ? `\n\n**Keywords:** ${draft.keywords.join(', ')}` : '';
    this.previewMarkdown = draft.markdown ?? `# ${draft.title}\n\nCreated: ${created}\n\nUpdated: ${updated}${kw}`;
    this.showPreview = true;
  }

  closePreview(): void {
    this.showPreview = false;
    this.previewMarkdown = '';
  }
}


