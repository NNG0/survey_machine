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

  uploadForWorkflow(file: File, requestStatus: RequestStatus): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('request_status_json', JSON.stringify(requestStatus));

    return this.http.post(`${this.baseUrl}/upload_for_workflow`, formData);
  }
}
