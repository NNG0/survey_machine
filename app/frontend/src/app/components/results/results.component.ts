import { Component, Input, OnInit } from "@angular/core";
import { CommonModule } from "@angular/common";
import { Router } from "@angular/router";
import { AppStateService } from "../../services/state/app-state.service";
import { Article, RawArticle } from "../../types/models";
import { ArticleStore } from "../../services/state/article.store";
import { PaperCardComponent } from "../paper-card/paper-card.component";

@Component({
  selector: "app-results",
  standalone: true,
  imports: [CommonModule, PaperCardComponent],
  templateUrl: "./results.component.html",
  styleUrls: ["./results.component.css"],
})
export class ResultsComponent {
  @Input() showResults = false;

  constructor(public appState: AppStateService) {}
}
