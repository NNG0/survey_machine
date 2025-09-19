import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PapersService, PaperCreate } from '../../services/papers.service';
import { RESTAPIService } from '../../restapiservice.service';
import { RequestStatus } from '../../types/models';

interface SavedPaper {
  id: string;
  title: string;
  authors: string;
  year: number;
  journal: string;
  abstract: string;
  relevance: number;
  tags: string[];
  citation: string;
  doi: string;
  savedAt: Date;
  // Additional optional fields for uploads
  filename?: string;
  contentPreview?: string;
}

@Component({
  selector: 'app-collection',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './collection.component.html',
  styleUrls: ['./collection.component.css']
})
export class CollectionComponent implements OnInit {
  savedPapers: SavedPaper[] = [];

  constructor(
    private papersService: PapersService,
    private workflowService: RESTAPIService
  ) {}

  ngOnInit() {
    this.loadSavedPapers();
  }

  loadSavedPapers() {
    this.papersService.getAllPapers().subscribe({
      next: (papers) => {
        this.savedPapers = papers.map(p => ({
          id: p.id,
          title: p.title,
          authors: p.authors,
          year: p.year,
          journal: 'Academic Journal',
          abstract: p.abstract,
          relevance: p.relevance || 0,
          tags: p.tags || [],
          citation: p.citation,
          doi: p.doi,
          savedAt: new Date(p.savedAt),
          filename: p.original_filename,
          contentPreview: p.abstract
        }));
      },
      error: (error) => {
        console.error('Error loading papers:', error);
        // Fallback to localStorage if API fails
        this.loadFromLocalStorage();
      }
    });
  }

  private loadFromLocalStorage() {
    const saved = localStorage.getItem('savedPapers');
    if (saved) {
      const parsed = JSON.parse(saved);
      this.savedPapers = parsed.map((p: any) => ({ ...p, savedAt: new Date(p.savedAt) }));
    }
  }

  persist() {
    localStorage.setItem('savedPapers', JSON.stringify(this.savedPapers));
  }

  removePaper(paperId: string) {
    this.papersService.deletePaper(paperId).subscribe({
      next: () => {
        this.savedPapers = this.savedPapers.filter(paper => paper.id !== paperId);
      },
      error: (error) => {
        console.error('Error deleting paper:', error);
        alert('Failed to delete paper');
      }
    });
  }

  removeAllPapers() {
    const confirmed = confirm('Delete all papers from your collection? This cannot be undone.');
    if (!confirmed) return;
    this.papersService.deleteAllPapers().subscribe({
      next: () => {
        this.savedPapers = [];
      },
      error: (error) => {
        console.error('Error deleting all papers:', error);
        alert('Failed to delete all papers');
      }
    });
  }

  private createWorkflowStatus(filename: string): RequestStatus {
    return {
      key_questions: null,
      papers: [],
      draft: [],
      settings: {
        research_question: `Analysis of ${filename}`,
        paper_limit: 5,
        num_key_questions: 5
      }
    };
  }

  startDrafting() {
    console.log('Starting drafting process...');
    // TODO: Implement drafting workflow
    alert('Drafting feature coming soon!');
  }

  onFileSelected(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files && input.files[0];
  if (!file) return;

  if (file.type !== 'application/pdf') {
    alert('Only PDF files are supported');
    input.value = '';
    return;
  }

  const workflowStatus = this.createWorkflowStatus(file.name);
  this.workflowService.uploadForWorkflow(file, workflowStatus).subscribe({
    next: (response) => {
      console.log('Workflow status updated:', response.request_status);

      // Kompletten Workflow starten
      this.runCompleteWorkflow(response.request_status);

      input.value = ''; // Reset file input
    },
    error: (workflowError) => {
      console.error('Workflow upload failed:', workflowError);
      alert('Failed to upload for workflow');
    },
  });
  }

  private runCompleteWorkflow(status: RequestStatus) {
    this.workflowService.runSingleNextStep(status).subscribe({
      next: ([updatedStatus, info]) => {
        console.log('Workflow step completed:', info);

        // Check if workflow is done (no more steps)
        if (info.warnings?.some(w => w.includes('No more steps'))) {
          console.log('🎉 Workflow completed successfully!');
          this.loadSavedPapers(); // Refresh UI
          return;
        }

        // Continue with next step
        setTimeout(() => {
          this.runCompleteWorkflow(updatedStatus);
        }, 500); // Small delay to avoid overwhelming the server
      },
      error: (err) => {
        console.error('Workflow step failed:', err);
        // Stop on error, but don't crash
      }
    });
  }
}

