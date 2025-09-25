import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PapersService, PaperCreate } from '../../services/papers.service';
import { Router } from '@angular/router';
import { ProjectsService } from '../../services/projects.service';
import { FormsModule } from '@angular/forms';
import { AppStateService } from '../../services/state/app-state.service';
import { ArticleStore } from '../../services/state/article.store';
import { PaperCardComponent } from '../paper-card/paper-card.component';
import { RESTAPIService } from '../../services/restapiservice.service';
import { Article, RequestStages, StepInformation } from '../../types/models';

@Component({
  selector: 'app-collection',
  standalone: true,
  imports: [CommonModule, FormsModule, PaperCardComponent],
  templateUrl: './collection.component.html',
  styleUrls: ['./collection.component.css'],
})
export class CollectionComponent implements OnInit {
  showDraftModal = false;
  showRQModal = false;
  uploadedFile: File | null = null;
  researchQuestions: string[] = [''];

  constructor(private papersService: PapersService, private draftsService: ProjectsService, private router: Router, public appState: AppStateService, private articleStore: ArticleStore, private restApi: RESTAPIService) { }

  ngOnInit() {
    this.articleStore.replaceArticlesWithSaved();
  }

  removePaper(article: Article) {
    const id = article?.article?.id ?? article?.article?.url ?? article?.article?.title;
    if (!id) {
      console.warn('Cannot remove paper without identifier', article);
      return;
    }

    this.articleStore.removePaperById(id);

    const updatedStatus = structuredClone(this.appState.currentStep.status);
    const workflowId = this.appState.currentWorkflowId;

    const persistence$ = workflowId
      ? this.restApi.updateWorkflowStatus(workflowId, updatedStatus)
      : this.restApi.createWorkflowStatus(updatedStatus);

    persistence$.subscribe({
      next: (persisted) => {
        if (persisted?.workflow_id) {
          this.appState.setWorkflowId(persisted.workflow_id);
        }
      },
      error: (error) => {
        console.warn('Failed to persist workflow after removal:', error);
      }
    });
  }

  removeAllPapers() {
    const confirmed = confirm(
      'Delete all papers from your collection? This cannot be undone.'
    );
    if (!confirmed) return;
    this.appState.removeAllPapers();
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];

    if (!file || file.type !== 'application/pdf') {
      console.error('No PDF file selected');
      return;
    }

    // Check if research question exists
    const currentRQ = this.appState.currentStep.status.settings.research_question?.trim();
    console.log('Current research question:', currentRQ);
    console.log('Will show popup:', !currentRQ);

    if (!currentRQ) {
      this.uploadedFile = file;
      this.researchQuestions = ['']; // Reset research questions
      this.showRQModal = true;
      console.log('Showing RQ modal');
      return;
    }

    this.performUpload(file, input);
  }

  private performUpload(file: File, input?: HTMLInputElement) {
    console.log('Uploading PDF:', file.name);

    const status = structuredClone(this.appState.currentStep.status);
    const workflowId = this.appState.currentWorkflowId;

    this.restApi.uploadForWorkflow(file, status, workflowId).subscribe({
      next: (response) => {
        console.log('Upload response:', response);

        if (response.request_status) {
          const stepInfo: StepInformation = {
            warnings: [],
            errors: [],
          };

          const stage = response.workflow_finished ? RequestStages.FINISHED : undefined;
          this.appState.hydrateFromBackend(response.request_status, stepInfo, stage);
        }

        if (response.workflow_id) {
          this.appState.setWorkflowId(response.workflow_id);
        }

        alert('PDF erfolgreich hochgeladen! Relevance Score wird berechnet...');
      },
      error: (err) => {
        console.error('Upload failed:', err);
        alert('Upload fehlgeschlagen: ' + (err.error?.detail || err.message));
      },
      complete: () => {
        if (input) input.value = ''; // Reset file input
      },
    });

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

  closeRQModal() {
    this.showRQModal = false;
    this.uploadedFile = null;
  }

  submitRQAndUpload() {
    const rq = this.researchQuestions[0]?.trim();
    if (!rq || !this.uploadedFile) {
      alert('Please enter a research question.');
      return;
    }

    // Update AppState with research question
    this.appState.state.update(prev => ({
      ...prev,
      current_step: {
        ...prev.current_step,
        status: {
          ...prev.current_step.status,
          settings: {
            ...prev.current_step.status.settings,
            research_question: rq
          }
        }
      }
    }));

    // Now perform the upload
    this.performUpload(this.uploadedFile);

    this.closeRQModal();
  }

  submitDraft() {
    const trimmed = this.researchQuestions
      .map((q) => (q || '').trim())
      .filter((q) => q.length > 0);

    if (trimmed.length === 0) {
      alert('Please provide at least one research question.');
      return;
    }

    const first = trimmed[0];
    const title = `Draft: ${first}`;
    const draft = this.draftsService.create(title, first, trimmed.length > 1 ? trimmed.slice(1) : null);
    if (trimmed.length > 0) {
      // ggf. hier Logik für mehrere Fragen einfügen
    }

    this.showDraftModal = false;
    this.router.navigate(['/projects', draft.id]);
  }

  trackByIndex(index: number): number {
    return index;
  }
}
