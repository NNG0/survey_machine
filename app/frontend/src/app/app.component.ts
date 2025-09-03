import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { HeaderComponent } from './components/header/header.component';
import { HeroComponent } from './components/hero/hero.component';
import { ResultsComponent } from './components/results/results.component';
import { TopicsComponent } from './components/topics/topics.component';
import { FooterComponent } from './components/footer/footer.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    HeaderComponent,
    HeroComponent,
    ResultsComponent,
    TopicsComponent,
    FooterComponent
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  showResults = false;
  showTopics = false;

  constructor(public router: Router) {}

  onSearch(searchData: {query: string, filters: any}) {
    this.showResults = true;
    this.showTopics = true;
    console.log('Search query:', searchData.query);
    console.log('Search filters:', searchData.filters);
  }
}
