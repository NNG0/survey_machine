import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-hero',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './hero.component.html',
  styleUrls: ['./hero.component.css']
})
export class HeroComponent {
  searchQuery: string = '';
  @Output() search = new EventEmitter<string>();

  onSearch() {
    if (this.searchQuery.trim().length > 0) {
      this.search.emit(this.searchQuery);
    }
  }
}
