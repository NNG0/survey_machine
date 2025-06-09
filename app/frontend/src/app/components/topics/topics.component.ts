import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-topics',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './topics.component.html',
  styleUrls: ['./topics.component.css']
})
export class TopicsComponent {
  @Input() showTopics: boolean = false;
}
