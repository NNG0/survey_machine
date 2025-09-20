import { Component, Input, OnInit } from "@angular/core";
import { CommonModule } from "@angular/common";
import { Router } from '@angular/router';

interface Paper {
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
}

@Component({
  selector: "app-results",
  standalone: true,
  imports: [CommonModule],
  templateUrl: "./results.component.html",
  styleUrls: ["./results.component.css"],
})
export class ResultsComponent implements OnInit {
  @Input() showResults = false;

  savedPaperIds = new Set<string>();

  constructor(private router: Router) {}

  exampleResult: Paper = {
    id: '1',
    title: 'Example Research Paper Title',
    authors: 'John Doe, Jane Smith',
    year: 2023,
    journal: 'Journal of Example Research',
    abstract: 'This is an example abstract for a research paper. It provides a brief overview of the research conducted and the main findings.',
    relevance: 85,
    tags: ['Machine Learning', 'AI', 'Research'],
    citation: 'Doe, J., & Smith, J. (2023). Example Research Paper Title. Journal of Example Research, 15(2), 123-145.',
    doi: 'https://doi.org/10.1000/example'
  };

  ngOnInit() {
    this.refreshSavedIds();
  }

  private refreshSavedIds() {
    const saved = localStorage.getItem('savedPapers');
    this.savedPaperIds.clear();
    if (saved) {
      try {
        const arr = JSON.parse(saved) as Array<{ id: string }>;
        for (const p of arr) this.savedPaperIds.add(p.id);
      } catch {
        // ignore parse errors
      }
    }
  }

  isSaved(paper: Paper): boolean {
    return this.savedPaperIds.has(paper.id);
  }

  toggleSave(paper: Paper) {
    const savedRaw = localStorage.getItem('savedPapers');
    let saved: any[] = [];
    if (savedRaw) {
      try { saved = JSON.parse(savedRaw); } catch { saved = []; }
    }

    if (this.isSaved(paper)) {
      // remove
      saved = saved.filter((p: any) => p.id !== paper.id);
      localStorage.setItem('savedPapers', JSON.stringify(saved));
      this.savedPaperIds.delete(paper.id);
    } else {
      // save
      const paperToSave = { ...paper, savedAt: new Date() };
      // avoid duplicates just in case
      const exists = saved.some((p: any) => p.id === paper.id);
      if (!exists) {
        saved.push(paperToSave);
        localStorage.setItem('savedPapers', JSON.stringify(saved));
        this.savedPaperIds.add(paper.id);
      }
    }
  }
}
