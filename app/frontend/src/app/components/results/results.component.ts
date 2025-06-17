import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

interface SearchResult {
  title: string;
  authors: string;
  year: number;
  journal: string;
  relevance: number;
  abstract: string;
  tags: string[];
  citation: string;
  doi: string;
}

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './results.component.html',
  styleUrls: ['./results.component.css']
})
export class ResultsComponent {
  @Input() results: SearchResult[] = [];
  @Input() showResults: boolean = false;

  // Example result for demonstration
  exampleResult: SearchResult = {
    title: 'Klimawandel und marine Ökosysteme: Eine umfassende Analyse der Auswirkungen auf Korallenriffe',
    authors: 'Schmidt, M., Müller, A., & Weber, K.',
    year: 2022,
    journal: 'Journal of Marine Ecology',
    relevance: 98,
    abstract: 'Diese Studie untersucht die Auswirkungen des Klimawandels auf Korallenriffe weltweit und analysiert verschiedene Anpassungsstrategien zur Erhaltung dieser wichtigen Ökosysteme.',
    tags: ['Korallenriffe', 'Klimawandel', 'Meeresbiologie', 'Ökosystemschutz'],
    citation: 'Schmidt, M., Müller, A., & Weber, K. (2022). Klimawandel und marine Ökosysteme: Eine umfassende Analyse der Auswirkungen auf Korallenriffe. Journal of Marine Ecology, 45(3), 234–251.',
    doi: 'https://doi.org/10.1234/jme.2022.45.3.234'
  };
}
