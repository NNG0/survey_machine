import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { RequestStatus, StepInformation } from './types/models';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class RESTAPIService {
  private baseUrl = "http://localhost:8001";

  constructor(private http: HttpClient) { }

  runSingleNextStep(requestStatus: RequestStatus): Observable<[RequestStatus, StepInformation]> {
    return this.http.post<[RequestStatus, StepInformation]>(
      `${this.baseUrl}/run_single_next_step`,requestStatus 
    )
  }

  nextStep(requestStatus: RequestStatus): Observable<[string,string,string, RequestStatus]> {
    return this.http.post<[string,string,string, RequestStatus]>(
      `${this.baseUrl}/next_step`,requestStatus 
    )
  }
}
