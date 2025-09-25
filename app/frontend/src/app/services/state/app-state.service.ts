import { Injectable, signal } from "@angular/core";
import {
  AppState,
  HistoryEntry,
  RequestStages,
  RequestStatus,
  StepInformation,
  StepState,
} from "../../types/models";
import { initialAppState, orderedRequestStages } from "../../types/state";
import { ArticleStore } from "./article.store";

@Injectable({
  providedIn: "root",
})
export class AppStateService {
  constructor(
  ) { }
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

  hydrateFromBackend(
    requestStatus: RequestStatus,
    stepInformation: StepInformation | undefined,
    stageOverride?: RequestStages,
  ) {
    this.state.update(prev => ({
      ...prev,
      current_step: {
        ...prev.current_step,
        status: requestStatus,
        step_information: stepInformation ?? { warnings: [], errors: [] },
        stage: stageOverride ?? prev.current_step.stage,
        saved_papers: requestStatus?.papers ? [...requestStatus.papers] : [],
      },
    }));
  }

  resetState() {
    this.state.set(initialAppState);
    this.workflowId = null;
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

  get currentStep(): StepState {
    return this.state().current_step;
  }

  get history(): HistoryEntry[] {
    return this.state().history;
  }

  private workflowId: string | null = null;

  get currentWorkflowId(): string | null {
    return this.workflowId;
  }

  setWorkflowId(workflowId: string | null) {
    this.workflowId = workflowId;
  }
}
