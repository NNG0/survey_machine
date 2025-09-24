import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PapersService, PaperCreate } from '../../services/papers.service';
import { Router } from '@angular/router';
import { DraftsService } from '../../services/drafts.service';
import { FormsModule } from '@angular/forms';
import { AppStateService } from '../../services/state/app-state.service';
import { ArticleStore } from '../../services/state/article.store';

@Component({
  selector: 'app-collection',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './collection.component.html',
  styleUrls: ['./collection.component.css']
})
export class CollectionComponent implements OnInit {
  showDraftModal = false;
  researchQuestions: string[] = [''];

  constructor(private papersService: PapersService, private draftsService: DraftsService, private router: Router, public appState: AppStateService, private articleStore: ArticleStore) { }

  ngOnInit() {
    this.articleStore.replaceArticlesWithSaved();
  }

  removePaper(paperId: string) {
    this.articleStore.removePaperById(paperId)
  }

  removeAllPapers() {
    const confirmed = confirm('Delete all papers from your collection? This cannot be undone.');
    if (!confirmed) return;
    this.appState.removeAllPapers()
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files && input.files[0];
    if (!file) return;

    this.appState

    /*
    // First create paper in database
    const newPaper: PaperCreate = {
      title: file.name,
      authors: 'Local Upload',
      year: new Date().getFullYear(),
      abstract: 'PDF file uploaded',
    };

    this.papersService.createPaper(newPaper).subscribe({
      next: (response) => {
        const paperId = response.id;
        // Then upload the PDF file
        if (file.type === 'application/pdf') {
          this.papersService.uploadPDF(paperId, file).subscribe({
            next: () => {
              input.value = ''; // Reset file input
            },
            error: (error) => {
              console.error('Error uploading PDF:', error);
              alert('Failed to upload PDF');
            }
          });
        } else {
          input.value = '';
        }
      },
      error: (error) => {
        console.error('Error creating paper:', error);
        alert('Failed to create paper');
      }
    });
    */
  }

  startDrafting() {
    this.showDraftModal = true;
    if (!this.researchQuestions || this.researchQuestions.length === 0) {
      this.researchQuestions = [''];
    }
  }

  addResearchQuestion() {
    if (this.researchQuestions.length < 5) {
      this.researchQuestions.push('');
    }
  }

  removeResearchQuestion(index: number) {
    if (index > 0 && this.researchQuestions.length > 1) {
      this.researchQuestions.splice(index, 1);
    }
  }

  closeDraftModal() {
    this.showDraftModal = false;
  }

  submitDraft() {
    const trimmed = this.researchQuestions.map(q => (q || '').trim()).filter(q => q.length > 0);
    if (trimmed.length === 0) {
      alert('Please provide at least one research question.');
      return;
    }
    const first = trimmed[0];
    const title = `Draft: ${first}`;
    const draft = this.draftsService.create(title);
    if (trimmed.length > 0) {
    }
    this.showDraftModal = false;
    this.router.navigate(['/drafts', draft.id]);
  }

  trackByIndex(index: number): number {
    return index;
  }
}
