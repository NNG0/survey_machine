import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

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

  ngOnInit() {
    this.loadSavedPapers();
  }

  loadSavedPapers() {
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
    this.savedPapers = this.savedPapers.filter(paper => paper.id !== paperId);
    this.persist();
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files && input.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      const text = typeof reader.result === 'string' ? reader.result : '';
      const preview = text.slice(0, 400);
      const newPaper: SavedPaper = {
        id: `local-${Date.now()}`,
        title: file.name,
        authors: 'Local Upload',
        year: new Date().getFullYear(),
        journal: 'Local File',
        abstract: preview || 'Lokale Datei hinzugefügt.',
        relevance: 0,
        tags: ['Upload'],
        citation: `${file.name} (Lokale Datei)`,
        doi: '',
        savedAt: new Date(),
        filename: file.name,
        contentPreview: preview
      };
      this.savedPapers = [newPaper, ...this.savedPapers];
      this.persist();
      // reset file input so selecting same file again triggers change
      input.value = '';
    };
    reader.readAsText(file);
  }

  startDrafting() {
    // Placeholder: Wire this to your drafting flow later
    alert('Drafting started with ' + this.savedPapers.length + ' papers.');
  }
}
