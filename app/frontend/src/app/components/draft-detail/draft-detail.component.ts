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
  draft: DraftItem | undefined;
  titleEdit: string = '';

  constructor(private route: ActivatedRoute, private router: Router, private draftsService: DraftsService) {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.draft = this.draftsService.getById(id);
      if (this.draft) {
        this.titleEdit = this.draft.title;
      }
    }
  }

  save(): void {
    if (!this.draft) return;
    const updated = this.draftsService.update(this.draft.id, { title: this.titleEdit });
    if (updated) {
      this.draft = updated;
    }
  }

  delete(): void {
    if (!this.draft) return;
    this.draftsService.delete(this.draft.id);
    this.router.navigate(['/drafts']);
  }
}


