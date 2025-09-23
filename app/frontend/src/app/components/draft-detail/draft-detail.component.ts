import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { DraftItem, DraftsService } from '../../services/drafts.service';
import { RESTAPIService } from '../../restapiservice.service';
import { RequestStages } from '../../types/models';
import { marked } from 'marked';

@Component({
  selector: 'app-draft-detail',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './draft-detail.component.html',
  styleUrls: ['./draft-detail.component.css']
})
export class DraftDetailComponent {
  draft: DraftItem;
  titleEdit: string = '';
  private saveTimer: any;
  private readonly saveDelayMs = 500;
  isProcessing = false;
  isFetchingNext = false;
  nextStepInfo: { message: string; single_call_fn_name: string; all_call_fn_name: string; stage: RequestStages } | null = null;
  warnings: string[] = [];
  errors: string[] = [];
  draftMarkdownHtml: string | null = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private draftsService: DraftsService,
    private api: RESTAPIService,
  ) {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.draft = this.draftsService.getByIdOrCreate(id, 'Untitled Draft');
    } else {
      this.draft = this.draftsService.create('Untitled Draft');
    }
    this.titleEdit = this.draft.title;
    this.updateDraftMarkdown();
  }

  save(): void {
    const updated = this.draftsService.update(this.draft.id, );
    if (updated) {
      this.draft = updated;
    }
  }

  // Debounced auto-save for any requestStatus changes
  private scheduleAutoSave() {
    clearTimeout(this.saveTimer);
    this.saveTimer = setTimeout(() => {
      const updated = this.draftsService.update(this.draft.id);
      if (updated) {
        this.draft = updated;
      }
      this.updateDraftMarkdown();
    }, this.saveDelayMs);
  }

  // Hook this to any change events from the template
  onRequestStatusChange() {
    this.updateDraftMarkdown();
    this.scheduleAutoSave();
  }

  getNextStepInfo(): void {
    if (this.isProcessing || this.isFetchingNext) return;
    this.isFetchingNext = true;
    this.api.nextStep(this.draft.requestStatus).subscribe({
      next: (resp) => {
        const [message, single_call_fn_name, all_call_fn_name, stage] = resp;
        this.nextStepInfo = { message, single_call_fn_name, all_call_fn_name, stage };
      },
      error: (err) => {
        this.errors = [String(err)];
      },
      complete: () => {
        this.isFetchingNext = false;
        this.scheduleAutoSave();
      },
    });
  }

  executeNextStep(): void {
    if (this.isProcessing) return;
    this.isProcessing = true;
    this.warnings = [];
    this.errors = [];
    this.api.runSingleNextStep(this.draft.requestStatus).subscribe({
      next: ([newStatus, stepInfo]) => {
        this.draft.requestStatus = newStatus;
        this.warnings = stepInfo.warnings || [];
        this.errors = stepInfo.errors || [];
        const updated = this.draftsService.update(this.draft.id,    );
        if (updated) this.draft = updated;

        // Also update the next step info by calling nextStep again
        this.getNextStepInfo();
        this.updateDraftMarkdown();
      },
      error: (err) => {
        this.errors = [String(err)];
      },
      complete: () => {
        this.isProcessing = false;
      },
    });
  }

  delete(): void {
    this.draftsService.delete(this.draft.id);
    this.router.navigate(['/drafts']);
  }

  private updateDraftMarkdown(): void {
    try {
      const rs = this.draft.requestStatus;
      if (!rs || !Array.isArray(rs.draft)) {
        this.draftMarkdownHtml = null;
        return;
      }
      const md = rs.draft
        .map(h => `${h.title}\n\n${h.content ?? ''}`) // The title already has a leading #
        .join('\n\n');
      const html = marked.parse(md);
      this.draftMarkdownHtml = String(html);
    } catch {
      this.draftMarkdownHtml = null;
    }
  }
}


