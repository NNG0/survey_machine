import { Injectable, signal } from "@angular/core";
import {
  AppState,
  HistoryEntry,
  RequestStatus,
  StepInformation,
  StepState,
} from "./types/models";
import { initialAppState } from "./types/state";

@Injectable({
  providedIn: "root",
})
export class AppStateService {
  state = signal<AppState>(initialAppState);

  setCurrentStep(
    requestStatus: RequestStatus,
    stepInformation: StepInformation,
  ) {
    const current = this.state();

    const newHistoryEntry: HistoryEntry = {
      id: current.history.length + 1,
      state: current.current_step,
    };

    const new_step: StepState = {
      status: requestStatus,
      step_information: stepInformation,
    };

    this.state.set({
      current_step: new_step,
      history: [...current.history, newHistoryEntry],
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
