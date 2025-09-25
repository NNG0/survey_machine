import { Component, OnInit } from "@angular/core";
import { CommonModule } from "@angular/common";
import { RouterModule, Router } from "@angular/router";
import { HeaderComponent } from "./components/header/header.component";
import { HeroComponent } from "./components/hero/hero.component";
import { ResultsComponent } from "./components/results/results.component";
import { TopicsComponent } from "./components/topics/topics.component";
import { FooterComponent } from "./components/footer/footer.component";
import { Article, RawArticle, RequestStatus, StepInformation } from "./types/models";
import { initialRequestStatus } from "./types/state";
import { AppStateService } from "./services/state/app-state.service";
import { PapersService } from "./services/papers.service";
import { RESTAPIService } from "./services/restapiservice.service";
import { ArticleStore } from "./services/state/article.store";

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
export class AppComponent implements OnInit {
  constructor(
    private restApiService: RESTAPIService,
    private appState: AppStateService,
    public router: Router,
    private papersService: PapersService,
    private articleStore: ArticleStore,
  ) { }
  ngOnInit(): void {
    this.restApiService.getLatestWorkflowStatus().subscribe({
      next: (response) => {
        if (response?.exists && response.request_status) {
          const stepInfo: StepInformation = { warnings: [], errors: [] };
          this.appState.hydrateFromBackend(response.request_status, stepInfo);
          if (response.id) {
            this.appState.setWorkflowId(response.id);
          }
          this.showResults = true;
          this.showTopics = true;
        }
      },
      error: (error) => {
        console.warn('Failed to restore latest workflow status:', error);
      }
    });

    this.papersService.getAllPapers().subscribe({
      next: (papers: any[]) => {
        papers
          .map(p => this.mapLegacyPaper(p))
          .forEach(mapped => {
            const exists = this.appState.currentStep.status.papers.some(existing =>
              existing.article.id === mapped.article.id ||
              existing.article.url === mapped.article.url
            );

            if (!exists) {
              this.articleStore.addPaper(mapped);
            }
          });
      },
      error: (error) => {
        console.error('Error loading papers:', error);
      }
    });
  }

  showResults = false;
  showTopics = false;

  onSearch(searchData: { query: string, filters: any }) {
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

    this.restApiService.runSingleRelevantLiteratureAgent(requestStatus).subscribe({
      next: ([updatedStatus, info]) => {
        console.log("Updated status: ", updatedStatus);
        console.log("Info: ", info);

        this.appState.setCurrentStep(updatedStatus, info);

        this.restApiService.createWorkflowStatus(updatedStatus).subscribe({
          next: (persisted) => {
            if (persisted?.workflow_id) {
              this.appState.setWorkflowId(persisted.workflow_id);
            }
          },
          error: (persistError) => {
            console.warn('Failed to persist workflow status:', persistError);
          }
        });
      },
      error: (err) => {
        console.error("Error running step", err);
      },
    });
  }

  private mapLegacyPaper(paper: any): Article {
    const raw: RawArticle = {
      id: paper.id ?? crypto.randomUUID(),
      title: paper.title ?? null,
      author: paper.authors ?? null,
      savedAt: paper.savedAt ?? null,
      abstract: paper.abstract ?? null,
      url: paper.doi ?? paper.url ?? null,
      doi: paper.doi ?? null,
    };

    return {
      article: raw,
      problem_questions: paper.problem_questions ?? null,
      methods: paper.methods ?? null,
      relevance_score: paper.relevance_score ?? paper.relevance ?? 0,
    };
  }
}
