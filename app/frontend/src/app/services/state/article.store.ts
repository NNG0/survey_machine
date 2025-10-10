import { Injectable } from "@angular/core";
import { AppStateService } from "./app-state.service";
import { Article, StepState } from "../../types/models";
import { PapersService } from "../papers.service";
import { Observable, of } from "rxjs";
import { catchError, map, switchMap } from "rxjs/operators";
import { RESTAPIService } from "../restapiservice.service";

@Injectable({ providedIn: "root" })
export class ArticleStore {
  constructor(
    private app: AppStateService,
    private papersService: PapersService,
    private restApi: RESTAPIService,
  ) {}

  toggleSavedPaper(article: Article) {
    this.updateStep((step) => {
      const exists = step.saved_papers.some(
        (p) => p.article.id === article.article.id,
      );

      return {
        ...step,
        saved_papers: exists
          ? step.saved_papers.filter((p) => p.article.id !== article.article.id)
          : [...step.saved_papers, article],
      };
    });
  }

  replaceArticlesWithSaved() {
    this.updateStep((step) => ({
      ...step,
      status: { ...step.status, papers: [...step.saved_papers] },
    }));
  }

  removeAllPapers() {
    this.updateStep((step) => ({
      ...step,
      status: {
        ...step.status,
        papers: [],
      },
    }));
  }

  removePaperById(id: string): Observable<void> {
    // Update state first
    this.updateStep((step) => ({
      ...step,
      saved_papers: step.saved_papers.filter((p) => p.article.id !== id),
      status: {
        ...step.status,
        papers: step.status.papers.filter((p) => p.article.id !== id),
      },
    }));

    // Get updated status for persistence
    const updatedStatus = this.app.currentStep.status;
    const workflowId = this.app.currentWorkflowId;

    // Try to delete from DB (ignore errors for workflow papers)
    const dbDelete$ = this.papersService
      .deletePaper(id)
      .pipe(catchError(() => of(void 0)));

    // Persist workflow
    const persistence$ = workflowId
      ? this.restApi.updateWorkflowStatus(workflowId, updatedStatus)
      : this.restApi.createWorkflowStatus(updatedStatus);

    // Run both in parallel, return when persistence completes
    return persistence$.pipe(
      map((persisted) => {
        if (persisted?.workflow_id) {
          this.app.setWorkflowId(persisted.workflow_id);
        }
      }),
      catchError((error) => {
        console.warn("Failed to persist workflow after removal:", error);
        return of(void 0);
      }),
    );
  }

  addPaper(paper: Article) {
    this.updateStep((step) => ({
      ...step,
      status: { ...step.status, papers: [...step.status.papers, paper] },
    }));
  }

  isArticleSaved(article: Article): boolean {
    return this.app
      .state()
      .current_step.saved_papers.some(
        (p) => p.article.id === article.article.id,
      );
  }

  private updateStep(updater: (step: StepState) => StepState) {
    this.app.state.update((prev) => ({
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
