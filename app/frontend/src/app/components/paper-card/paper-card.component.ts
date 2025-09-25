import { Component, Input } from '@angular/core';
import { Article } from '../../types/models';
import { ArticleStore } from '../../services/state/article.store';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-paper-card',
  imports: [CommonModule],
  templateUrl: './paper-card.component.html',
  styleUrl: './paper-card.component.css'
})
export class PaperCardComponent {
  constructor(private articleStore: ArticleStore) { }
  @Input() paper!: Article;
  @Input() mode: 'results' | 'saved' = 'results';

  isSaved(): boolean {
    return this.articleStore.isArticleSaved(this.paper)
  }

  goToArticle(): string | null {
    if (this.paper.article.doi && this.paper.article.doi.trim() !== '')
    {
      return 'https://doi.org/' + this.paper.article.doi;
    } else if (this.paper.article.url && this.paper.article.url.trim() !== '') {
      return this.paper.article.url;
    } else {
      return null;
    }
  }

  toggleSave() {
    this.articleStore.toggleSavedPaper(this.paper)
  }

  removePaper() {
    this.articleStore.removePaperById(this.paper.article.id)
  }
}
