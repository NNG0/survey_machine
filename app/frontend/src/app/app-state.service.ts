import { Injectable, signal } from "@angular/core";
import {
  AppState,
  HistoryEntry,
  RequestStages,
  RequestStatus,
  StepInformation,
  StepState,
} from "./types/models";
import { initialAppState, orderedRequestStages } from "./types/state";

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
        current_step: {
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

  get currentStep(): StepState {
    return this.state().current_step;
  }

  get history(): HistoryEntry[] {
    return this.state().history;
  }
}
