import { Injectable } from "@angular/core";
import { AppStateService } from "./app-state.service";
import { DraftItem, StepState } from "../../types/models";

@Injectable({ providedIn: 'root' })
export class DraftsStore {
  constructor(private appState: AppStateService) {}

  createDraft() {
    const dummyDraft: DraftItem = {
      id: crypto.randomUUID(),
      title: "",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      content: null,
    };

    this.updateStep(step => ({
      ...step,
      status: { ...step.status, draft: [...step.status.draft, dummyDraft] },
    }));

    return dummyDraft.id;
  }

  removeDraft(id: string) {
    this.updateStep(step => ({
      ...step,
      status: {
        ...step.status,
        draft: step.status.draft.filter(d => d.id !== id),
      },
    }));
  }

  getDraftById(id: string) {
    return this.appState.state().current_step.status.draft.find(
      (d: DraftItem) => d.id === id
    );
  }

  getArrayOfDrafts() {
    return this.appState.state().current_step.status.draft;
  }

  private updateStep(updater: (step: StepState) => StepState) {
    this.appState.state.update((prev: any) => ({
      ...prev,
      current_step: updater(prev.current_step),
    }));
  }
}
