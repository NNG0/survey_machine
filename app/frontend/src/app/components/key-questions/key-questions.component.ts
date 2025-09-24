import { Component } from '@angular/core';
import { AppStateService } from '../../services/state/app-state.service';
import { RequestStatus } from '../../types/models';
import { RESTAPIService } from '../../services/restapiservice.service';

@Component({
  selector: 'app-key-questions',
  imports: [],
  templateUrl: './key-questions.component.html',
  styleUrl: './key-questions.component.css'
})
export class KeyQuestionsComponent {
  constructor(
    public appState: AppStateService,
    private restApiService: RESTAPIService,
             ) {}

  triggerLiteratureSearch() {
    let requestStatus: RequestStatus = this.appState.currentStep.status
    this.restApiService.runSingleNextStep(requestStatus).subscribe({
      next: ([updatedStatus, info]) => {
        console.log("Updated status: ", updatedStatus);
        console.log("Info: ", info);

        this.appState.setCurrentStep(updatedStatus, info);
      },
      error: (err) => {
        console.error("Error running step", err);
      },

    })
  }
}
