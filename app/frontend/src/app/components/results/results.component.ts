import { Component, Input, OnInit } from "@angular/core";
import { CommonModule } from "@angular/common";
import { Router } from '@angular/router';
import { AppStateService } from "../../services/state/app-state.service";
import { Article, RawArticle } from "../../types/models";
import { ArticleStore } from "../../services/state/article.store";

@Component({
  selector: "app-results",
  standalone: true,
  imports: [CommonModule],
  templateUrl: "./results.component.html",
  styleUrls: ["./results.component.css"],
})
export class ResultsComponent {
  @Input() showResults = false;

  constructor(private router: Router, public appState: AppStateService, private articleStore: ArticleStore) {}

  isSaved(article: Article): boolean {
    return this.articleStore.isArticleSaved(article)
  }

  toggleSave(article: Article) {
    this.articleStore.toggleSavedPaper(article)
  }

  goToArticle(article: RawArticle) {
    return article.doi ? `https://doi.org/${article.doi}` : article.url
  }
}
