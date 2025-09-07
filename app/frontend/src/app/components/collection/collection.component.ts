import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PapersService, PaperCreate } from '../../services/papers.service';

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

  constructor(private papersService: PapersService) {}

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

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files && input.files[0];
    if (!file) return;

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
              this.loadSavedPapers(); // Reload to show new paper
              input.value = ''; // Reset file input
            },
            error: (error) => {
              console.error('Error uploading PDF:', error);
              alert('Failed to upload PDF');
            }
          });
        } else {
          this.loadSavedPapers(); // Just reload for non-PDF files
          input.value = '';
        }
      },
      error: (error) => {
        console.error('Error creating paper:', error);
        alert('Failed to create paper');
      }
    });
  }

  startDrafting() {
    // Placeholder: Wire this to your drafting flow later
    alert('Drafting started with ' + this.savedPapers.length + ' papers.');
  }
}
