import { Injectable, Optional } from '@angular/core';
import { RequestStatus, StatusSetting, SurveyResult } from '../types/models';
import { initialRequestStatus } from '../types/state';

export interface DraftItem {
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
export class DraftsService {
  private storageKey = 'drafts';

  private readAll(): DraftItem[] {
    const raw = localStorage.getItem(this.storageKey);
    if (!raw) return [];
    try {
      return JSON.parse(raw) as DraftItem[];
    } catch {
      return [];
    }
  }

  private writeAll(items: DraftItem[]): void {
    localStorage.setItem(this.storageKey, JSON.stringify(items));
  }

  getAll(): DraftItem[] {
    return this.readAll().sort((a, b) => (b.updatedAt > a.updatedAt ? 1 : -1));
  }

  getById(id: string): DraftItem | undefined {
    return this.readAll().find(d => d.id === id);
  }

  getByIdOrCreate(id: string, default_title: string): DraftItem {
    return this.getById(id) || this.create(default_title, "", null);
  }

  create(title: string, research_question: string, key_questions: string[] | null): DraftItem {
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
      papers: [],
      draft: [],
      
    }
    const item: DraftItem = {
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
    //updates: Partial<Pick<DraftItem, 'title' | NewType | 'status' | 'markdown' | 'requestStatus'>>
  ): DraftItem | undefined {
    const items = this.readAll();
    const idx = items.findIndex(d => d.id === id);
    if (idx === -1) return undefined;
    /*const updated: DraftItem = { ...items[idx], ...updates, updatedAt: new Date().toISOString() };
    items[idx] = updated;
    this.writeAll(items);
    */
    return undefined;
  }

  delete(id: string): void {
    const items = this.readAll().filter(d => d.id !== id);
    this.writeAll(items);
  }
}


