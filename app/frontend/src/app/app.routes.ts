import { Routes } from '@angular/router';
import { CollectionComponent } from './components/collection/collection.component';
import { DraftsComponent } from './components/drafts/drafts.component';
import { DraftDetailComponent } from './components/draft-detail/draft-detail.component';

export const routes: Routes = [
  {
    path: 'collection',
    component: CollectionComponent
  },
  {
    path: 'drafts',
    component: DraftsComponent
  },
  {
    path: 'drafts/:id',
    component: DraftDetailComponent
  }
];
