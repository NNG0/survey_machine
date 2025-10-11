import { Component, OnInit } from "@angular/core";
import { CommonModule } from "@angular/common";
import { RouterModule, Router } from "@angular/router";
import { HeaderComponent } from "./components/header/header.component";
import { HeroComponent } from "./components/hero/hero.component";
import { ResultsComponent } from "./components/results/results.component";
import { TopicsComponent } from "./components/topics/topics.component";
import { FooterComponent } from "./components/footer/footer.component";
import {
  Article,
  OpenAlexResult,
  RawArticle,
  RequestStatus,
  StepInformation,
} from "./types/models";
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
  ) {}
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
        console.warn("Failed to restore latest workflow status:", error);
      },
    });

    this.papersService.getAllPapers().subscribe({
      next: (papers: any[]) => {
        papers
          .map((p) => this.mapLegacyPaper(p))
          .forEach((mapped) => {
            const exists = this.appState.currentStep.status.papers.some(
              (existing) =>
                existing.article.id === mapped.article.id ||
                existing.article.url === mapped.article.url,
            );

            if (!exists) {
              this.articleStore.addPaper(mapped);
            }
          });
      },
      error: (error) => {
        console.error("Error loading papers:", error);
      },
    });
  }

  showResults = false;
  showTopics = false;
  isLoading = false;

  onSearch(searchData: { query: string; filters: any }) {
    let requestStatus: RequestStatus = {
      ...initialRequestStatus,
      settings: {
        ...initialRequestStatus.settings,
        research_question: searchData.query,
      },
    };

    this.showResults = true;
    this.showTopics = false;
    this.isLoading = true;

    console.log("Search query:", searchData.query);
    console.log("RequestStatus:", requestStatus);
    console.log("Search filters:", searchData.filters);

    this.restApiService
      // .runSingleRelevantLiteratureAgent(requestStatus)
      // .subscribe({
      //   next: ([updatedStatus, info]) => {
      //     console.log("Updated status: ", updatedStatus);
      //     console.log("Info: ", info);

      //     this.appState.setCurrentStep(updatedStatus, info);
      //     this.appState.saveLiteratureSearchResults();
      //     this.articleStore.removeAllPapers();

      //     this.restApiService.createWorkflowStatus(updatedStatus).subscribe({
      //       next: (persisted) => {
      //         if (persisted?.workflow_id) {
      //           this.appState.setWorkflowId(persisted.workflow_id);
      //         }
      //       },
      //       error: (persistError) => {
      //         console.warn("Failed to persist workflow status:", persistError);
      //       },
      //     });

      //     this.isLoading = false;
      //     this.showTopics = true;
      //   },
      //   error: (err) => {
      //     console.error("Error running step", err);
      //     this.isLoading = false;
      //     this.showTopics = true;
      //   },
      // });
      .searchOpenAlex(searchData.query)
      .subscribe({
        next: (response) => {
          console.log("OpenAlex search results:", response);
          // To simplify, we'll construct an updated status with the new papers. Note that optimally, the RequestStatus should not be used in this case. 
          var updatedStatus: RequestStatus = {
            ...requestStatus,
            papers: response.results.map((paper: OpenAlexResult) => {
              const raw: RawArticle = {
                id: "OPENALEX" +paper.id,
                title: paper.title,
                author: (paper.authors && paper.authors.length > 0) ? paper.authors[0] : null,
                savedAt: paper.published_date,
                abstract: paper.abstract,
                url: paper.pdf_url,
                doi: null,
              }
              return {
                article: raw, problem_questions: null, methods: null, relevance_score: paper.fcwi || 0
              };
            }),
          }
          console.log("Updated status: ", updatedStatus);
          // But we don't have step info from this, so just don't change it.
          this.appState.setCurrentStep(updatedStatus, {warnings: [], errors: []});
          this.appState.saveLiteratureSearchResults();
          this.articleStore.removeAllPapers(); // Is this correct? It might remove all papers, as the name suggests.
          this.restApiService.createWorkflowStatus(updatedStatus).subscribe({
            next: (persisted) => {
              if (persisted?.workflow_id) {
                this.appState.setWorkflowId(persisted.workflow_id);
              }
            },
            error: (persistError) => {
              console.warn("Failed to persist workflow status:", persistError);
            },
          });

          this.isLoading = false;
          this.showTopics = true;
        },
        error: (error) => {
          console.error("Error searching OpenAlex:", error);
          this.isLoading = false;
          this.showTopics = true;
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
