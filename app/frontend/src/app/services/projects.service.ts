import { Injectable, Optional } from '@angular/core';
import { Article, RequestStatus, StatusSetting, SurveyResult } from '../types/models';
import { initialRequestStatus } from '../types/state';

export interface ProjectItem {
  id: string;
  title: string;
  createdAt: string; // ISO string
  updatedAt: string; // ISO string
  keywords?: string[];
  markdown?: string;
  requestStatus: RequestStatus;
}

type NewType = 'keywords';

@Injectable({ providedIn: 'root' })
export class ProjectsService {
  private storageKey = 'drafts'; // This stays the same for backward compatibility

  private readAll(): ProjectItem[] {
    const raw = localStorage.getItem(this.storageKey);
    if (!raw) return [];
    try {
      return JSON.parse(raw) as ProjectItem[];
    } catch {
      return [];
    }
  }

  private writeAll(items: ProjectItem[]): void {
    localStorage.setItem(this.storageKey, JSON.stringify(items));
  }

  getAll(): ProjectItem[] {
    return this.readAll().sort((a, b) => (b.updatedAt > a.updatedAt ? 1 : -1));
  }

  getById(id: string): ProjectItem | undefined {
    return this.readAll().find(d => d.id === id);
  }

  getByIdOrCreate(id: string, default_title: string): ProjectItem {
    return this.getById(id) || this.create(default_title, "", null, []);
  }

  create(title: string, research_question: string, key_questions: string[] | null, papers: Article[]): ProjectItem {
    const now = new Date().toISOString();
    const statusSettings: StatusSetting = {
      research_question,
      paper_limit: 5,
      num_key_questions: 5,
    };
    
    
    // If the key questions are provided as a list of strings, map them to a list of [string, null, null]
    let processed_key_questions: [string, string[] | null, SurveyResult | null][] | null = null;
    if (key_questions && key_questions.length > 0 && typeof key_questions[0] === 'string') {
      processed_key_questions = key_questions.map(q => [q, null, null]);
    } 

    const requestStatus: RequestStatus = {
      settings: statusSettings,
      key_questions: processed_key_questions,
      papers: papers,
      draft: [],
      
    }
    const item: ProjectItem = {
      id: crypto.randomUUID(),
      title,
      createdAt: now,
      updatedAt: now,
      keywords: [],
      requestStatus: { ...initialRequestStatus, ...requestStatus },
    };
    const items = this.readAll();
    items.unshift(item);
    this.writeAll(items);
    return item;
  }

  update(
    id: string,
    updates: Partial<Pick<ProjectItem, 'title' | NewType | 'markdown' | 'requestStatus'>>
  ): ProjectItem | undefined {
    const items = this.readAll();
    const idx = items.findIndex(d => d.id === id);
    if (idx === -1) return undefined;
    const updated: ProjectItem = { ...items[idx], ...updates, updatedAt: new Date().toISOString() };
    items[idx] = updated;
    this.writeAll(items);
    return undefined;
  }

  delete(id: string): void {
    const items = this.readAll().filter(d => d.id !== id);
    this.writeAll(items);
  }
}


