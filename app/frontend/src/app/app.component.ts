import { Component } from "@angular/core";
import { CommonModule } from "@angular/common";
import { RouterModule, Router } from "@angular/router";
import { HeaderComponent } from "./components/header/header.component";
import { HeroComponent } from "./components/hero/hero.component";
import { ResultsComponent } from "./components/results/results.component";
import { TopicsComponent } from "./components/topics/topics.component";
import { FooterComponent } from "./components/footer/footer.component";
import { RESTAPIService } from "./restapiservice.service";
import { RequestStatus } from "./types/models";
import { initialRequestStatus } from "./types/state";
import { AppStateService } from "./app-state.service";

@Component({
  selector: "app-root",
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    HeaderComponent,
    HeroComponent,
    ResultsComponent,
    TopicsComponent,
    FooterComponent,
  ],
  templateUrl: "./app.component.html",
  styleUrls: ["./app.component.css"],
})
export class AppComponent {
  constructor(
    private restApiService: RESTAPIService,
    private appState: AppStateService,
  ) {}
  showResults = false;
  showTopics = false;

  onSearch(searchData: {query: string, filters: any}) {
    let requestStatus: RequestStatus = {
      ...initialRequestStatus,
      settings: {
        ...initialRequestStatus.settings,
        research_question: searchData.query,
      },
    };
    
    this.showResults = true;
    this.showTopics = true;

    console.log("Search query:", searchData.query);
    console.log("RequestStatus:", requestStatus);
    console.log("Search filters:", searchData.filters);

    this.restApiService.runAllCreateKeyQuestions(requestStatus).subscribe({
      next: ([updatedStatus, info]) => {
        console.log("Updated status: ", updatedStatus);
        console.log("Info: ", info);

        // TODO: update state
        this.appState.setCurrentStep(updatedStatus, info);
      },
      error: (err) => {
        console.error("Error running step", err);
      },
    });
  }
}
