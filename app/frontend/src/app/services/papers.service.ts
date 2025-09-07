import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface PaperCreate {
  title: string;
  authors?: string;
  abstract?: string;
  url?: string;
  year?: number;
  relevance_score?: number;
  cluster_id?: number;
  cluster_label?: string;
}

@Injectable({
  providedIn: 'root'
})
export class PapersService {
  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  getAllPapers(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/papers`);
  }

  createPaper(paper: PaperCreate): Observable<any> {
    return this.http.post(`${this.apiUrl}/papers`, paper);
  }

  deletePaper(id: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/papers/${id}`);
  }

  deleteAllPapers(): Observable<any> {
    return this.http.delete(`${this.apiUrl}/papers`);
  }

  uploadPDF(paperId: number, file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.apiUrl}/papers/${paperId}/upload-pdf`, formData);
  }

  getPaperFile(paperId: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/papers/${paperId}/file`);
  }
}