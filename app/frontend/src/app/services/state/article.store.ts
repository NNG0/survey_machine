import { Injectable } from "@angular/core";
import { AppStateService } from "./app-state.service";
import { Article, StepState } from "../../types/models";

@Injectable({ providedIn: 'root' })
export class ArticleStore {
  constructor(private app: AppStateService) {}

  toggleSavedPaper(article: Article) {
    this.updateStep(step => {
      const exists = step.saved_papers.some(p => p.article.id === article.article.id);

      return {
        ...step,
        saved_papers: exists
          ? step.saved_papers.filter(p => p.article.id !== article.article.id)
          : [...step.saved_papers, article],
      };
    });
  }

  replaceArticlesWithSaved() {
    this.updateStep(step => ({
      ...step,
      status: { ...step.status, papers: [...step.saved_papers] },
    }));
  }

  removePaperById(id: string) {
    this.updateStep(step => ({
      ...step,
      saved_papers: step.saved_papers.filter(p => !this.isSameArticle(p, id)),
      status: {
        ...step.status,
        papers: step.status.papers.filter(p => !this.isSameArticle(p, id)),
      },
    }));
  }

  addPaper(paper: Article) {
    this.updateStep(step => ({
      ...step,
      status: { ...step.status, papers: [...step.status.papers, paper] },
    }));
  }

  isArticleSaved(article: Article): boolean {
    return this.app.state().current_step.saved_papers
      .some(p => p.article.id === article.article.id);
  }

  private updateStep(updater: (step: StepState) => StepState) {
    this.app.state.update(prev => ({
      ...prev,
      current_step: updater(prev.current_step),
    }));
  }

  private isSameArticle(article: Article, identifier: string): boolean {
    return (
      article.article.id === identifier ||
      article.article.url === identifier ||
      article.article.title === identifier
    );
  }
}
