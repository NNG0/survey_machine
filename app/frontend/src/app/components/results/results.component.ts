import { Component, Input, OnInit } from "@angular/core";
import { CommonModule } from "@angular/common";
import { Router } from '@angular/router';
import { AppStateService } from "../../app-state.service";
import { Article } from "../../types/models";

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
export class ResultsComponent {
  @Input() showResults = false;

  constructor(private router: Router, public appState: AppStateService) {}

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

  isSaved(article: Article): boolean {
    return this.appState.isArticleSaved(article)
  }

  toggleSave(article: Article) {
    this.appState.toggleSavedPaper(article)
  }
}
