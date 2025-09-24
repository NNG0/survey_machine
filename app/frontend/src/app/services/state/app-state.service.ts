import { Injectable, signal } from "@angular/core";
import {
  AppState,
  Article,
  DraftItem,
  HistoryEntry,
  RequestStages,
  RequestStatus,
  StepInformation,
  StepState,
} from "../../types/models";
import { initialAppState, orderedRequestStages } from "../../types/state";

@Injectable({
  providedIn: "root",
})
export class AppStateService {
  state = signal<AppState>(initialAppState);

  private getNextStage(currentStage: RequestStages): RequestStages {
    const currentIndex = orderedRequestStages.indexOf(currentStage)

    return currentIndex >= orderedRequestStages.length - 1 ?
      currentStage : orderedRequestStages[currentIndex + 1]
  }

  private getPrevStage(currentStage: RequestStages): RequestStages {
    const currentIndex = orderedRequestStages.indexOf(currentStage)

    return currentIndex <= 0 ?
      currentStage : orderedRequestStages[currentIndex - 1]
  }

  setCurrentStep(
    requestStatus: RequestStatus,
    stepInformation: StepInformation,
  ) {
    this.state.update(prev => {
      const newHistoryEntry: HistoryEntry = {
        id: prev.history.length + 1,
        state: prev.current_step,
      };

      return {
        ...prev,
        current_step: {
          ...prev.current_step,
          stage: this.getNextStage(prev.current_step.stage),
          status: requestStatus,
          step_information: stepInformation,
        },
        history: [...prev.history, newHistoryEntry],
      }
    });
  }

  resetState() {
    this.state.set(initialAppState);
  }

  toggleSavedPaper(article: Article) {
    this.state.update(prev => {
      const saved = prev.current_step.saved_papers
      const exists = saved.some(p => p.article.id === article.article.id)

      return {
        ...prev,
        current_step: {
          ...prev.current_step,
          saved_papers: exists
            ? saved.filter(p => p.article.id !== article.article.id)
            : [...saved, article]
        }
      }
    })
  }

  replaceArticlesWithSaved() {
    this.state.update(prev => {
      return {
        ...prev,
        current_step: {
          ...prev.current_step,
          status: {
            ...prev.current_step.status,
            papers: [...prev.current_step.saved_papers]
          }
        }
      }
    })
  }

  replaceArticlesAndRemoveSaved() {
    this.state.update(prev => {
      return {
        ...prev,
        current_step: {
          ...prev.current_step,
          saved_papers: [],
          status: {
            ...prev.current_step.status,
            papers: [...prev.current_step.saved_papers]
          }
        }
      }
    })
  }

  isArticleSaved(article: Article): boolean {
    return this.state().current_step.saved_papers.includes(article)
  }

  removeDraft(id: string) {
    this.state().current_step.status.draft.filter(d => d.id !== id)
  }

  createDraft() {
    const dummyDraft: DraftItem = {
      id: crypto.randomUUID(),
      title: "",
      createdAt: "",
      updatedAt: "",
      content: null
    }
    this.state().current_step.status.draft.push(dummyDraft)
    return dummyDraft.id
  }

  removeAllPapers() {
    this.state.update(prev => {
      return {
        ...prev,
        current_step: {
          ...prev.current_step,
          saved_papers: []
        }
      }
    })
  }

  removePaperById(id: string) {
    this.state().current_step.status.papers.filter(p => p.article.id !== id)
  }

  addPaper(paper: Article) {
    this.state().current_step.status.papers.push(paper)
  }

  getDraftById(id: string) {
    return this.getArrayOfDrafts().find(d => d.id === id)
  }

  getArrayOfDrafts() {
    return this.state().current_step.status.draft
  }

  get currentStep(): StepState {
    return this.state().current_step;
  }

  get history(): HistoryEntry[] {
    return this.state().history;
  }
}
