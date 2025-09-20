import { Injectable } from '@angular/core';

export interface DraftItem {
  id: string;
  title: string;
  createdAt: string; // ISO string
  updatedAt: string; // ISO string
  keywords?: string[];
  status: 'loading' | 'ready';
  markdown?: string;
}

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

  create(title: string): DraftItem {
    const now = new Date().toISOString();
    const item: DraftItem = {
      id: crypto.randomUUID(),
      title,
      createdAt: now,
      updatedAt: now,
      keywords: [],
      status: 'loading'
    };
    const items = this.readAll();
    items.unshift(item);
    this.writeAll(items);
    // Simulate background processing; mark as ready after a short delay
    setTimeout(() => {
      this.update(item.id, {
        status: 'ready',
        markdown: `# ${title}\n\nThis is a generated draft.\n\n- Created: ${new Date(item.createdAt).toLocaleString()}\n- Updated: ${new Date().toLocaleString()}`
      });
    }, 2000);
    return item;
  }

  update(id: string, updates: Partial<Pick<DraftItem, 'title' | 'keywords' | 'status' | 'markdown'>>): DraftItem | undefined {
    const items = this.readAll();
    const idx = items.findIndex(d => d.id === id);
    if (idx === -1) return undefined;
    const updated: DraftItem = { ...items[idx], ...updates, updatedAt: new Date().toISOString() };
    items[idx] = updated;
    this.writeAll(items);
    return updated;
  }

  delete(id: string): void {
    const items = this.readAll().filter(d => d.id !== id);
    this.writeAll(items);
  }
}


