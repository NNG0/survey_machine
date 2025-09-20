import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { DraftItem, DraftsService } from '../../services/drafts.service';

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

  constructor(private route: ActivatedRoute, private router: Router, private draftsService: DraftsService) {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.draft = this.draftsService.getByIdOrCreate(id, 'Untitled Draft');
    } else {
      this.draft = this.draftsService.create('Untitled Draft');
    }
    this.titleEdit = this.draft.title;
  }

  save(): void {
    const updated = this.draftsService.update(this.draft.id, { title: this.titleEdit });
    if (updated) {
      this.draft = updated;
    }
  }

  // Debounced auto-save for any requestStatus changes
  private scheduleAutoSave() {
    clearTimeout(this.saveTimer);
    this.saveTimer = setTimeout(() => {
      const updated = this.draftsService.update(this.draft.id, {
        title: this.titleEdit,
        requestStatus: this.draft.requestStatus,
      });
      if (updated) {
        this.draft = updated;
      }
    }, this.saveDelayMs);
  }

  // Hook this to any change events from the template
  onRequestStatusChange() {
    this.scheduleAutoSave();
  }

  delete(): void {
    this.draftsService.delete(this.draft.id);
    this.router.navigate(['/drafts']);
  }
}


