import { Routes } from "@angular/router";
import { AppComponent } from "./app.component";
import { CollectionComponent } from './components/collection/collection.component';
import { DraftsComponent } from './components/drafts/drafts.component';
import { DraftDetailComponent } from './components/draft-detail/draft-detail.component';

export const routes: Routes = [
  {
    path: 'collection',
    component: CollectionComponent
  },
  {
    path: 'drafts', // We leave the old routed active for now, the backend shouldn't change at this point in time. 
    component: DraftsComponent
  },
  {
    path: 'drafts/:id',
    component: DraftDetailComponent
  },
  {
    path: 'projects', // Because we switched from "drafts" to "projects" in the UI, we need to map the routes accordingly
    component: DraftsComponent
  },
  {
    path: 'projects/:id',
    component: DraftDetailComponent
  },
  {
    path: '',
    component: AppComponent,
    pathMatch: 'full'
  }
];
