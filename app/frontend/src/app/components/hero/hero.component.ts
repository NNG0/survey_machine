import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

interface SearchTerm {
  text: string;
  useOrOperator: boolean;
}

interface SearchFilters {
  yearFrom: number | null;
  yearTo: number | null;
  minCitations: number | null;
  titleTerms: SearchTerm[];
  abstractTerms: SearchTerm[];
  subject: string;
  useSemanticSearch: boolean;
}

@Component({
  selector: 'app-hero',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './hero.component.html',
  styleUrls: ['./hero.component.css']
})
export class HeroComponent {
  searchQuery: string = '';
  showFilters: boolean = false;
  filters: SearchFilters = {
    yearFrom: null,
    yearTo: null,
    minCitations: null,
    titleTerms: [{ text: '', useOrOperator: false }],
    abstractTerms: [{ text: '', useOrOperator: false }],
    subject: '',
    useSemanticSearch: true
  };

  @Output() search = new EventEmitter<{query: string, filters: SearchFilters}>();

  onSearch() {
    if (this.searchQuery.trim().length > 0) {
      this.search.emit({
        query: this.searchQuery,
        filters: this.filters
      });
    }
  }

  toggleFilters() {
    this.showFilters = !this.showFilters;
  }

  resetFilters() {
    this.filters = {
      yearFrom: null,
      yearTo: null,
      minCitations: null,
      titleTerms: [{ text: '', useOrOperator: false }],
      abstractTerms: [{ text: '', useOrOperator: false }],
      subject: '',
      useSemanticSearch: true
    };
  }

  addSearchTerm(type: 'title' | 'abstract') {
    if (type === 'title') {
      this.filters.titleTerms.push({ text: '', useOrOperator: false });
    } else {
      this.filters.abstractTerms.push({ text: '', useOrOperator: false });
    }
  }

  removeSearchTerm(type: 'title' | 'abstract', index: number) {
    if (type === 'title' && this.filters.titleTerms.length > 1) {
      this.filters.titleTerms.splice(index, 1);
    } else if (type === 'abstract' && this.filters.abstractTerms.length > 1) {
      this.filters.abstractTerms.splice(index, 1);
    }
  }
}
