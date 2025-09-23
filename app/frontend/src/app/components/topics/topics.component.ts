import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-topics',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './topics.component.html',
  styleUrls: ['./topics.component.css']
})
export class TopicsComponent {
  @Input() showTopics: boolean = false;

  constructor(private router: Router) {}

  navigateToCollection(): void {
    this.router.navigate(['/collection']);
  }
}
