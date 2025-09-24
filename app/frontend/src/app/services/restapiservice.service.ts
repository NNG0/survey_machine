import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { Observable } from "rxjs";
import { RequestStages, RequestStatus, StepInformation } from "../types/models";

@Injectable({
  providedIn: "root",
})
export class RESTAPIService {
  private baseUrl = "http://localhost:8001";

  constructor(private http: HttpClient) { }

  runSingleNextStep(
    requestStatus: RequestStatus,
  ): Observable<[RequestStatus, StepInformation]> {
    return this.http.post<[RequestStatus, StepInformation]>(
      `${this.baseUrl}/run_single_next_step`,
      requestStatus,
    );
  }

  runSingleRelevantLiteratureAgent(requestStatus: RequestStatus): Observable<[RequestStatus, StepInformation]> {
    return this.http.post<[RequestStatus, StepInformation]>(
      `${this.baseUrl}/run_all_relevant_literature`,
      requestStatus,
    );
  }

  runAllCreateKeyQuestions(
    requestStatus: RequestStatus,
  ): Observable<[RequestStatus, StepInformation]> {
    return this.http.post<[RequestStatus, StepInformation]>(
      `${this.baseUrl}/run_all_create_key_questions`,
      requestStatus,
    );
  }

  nextStep(
    requestStatus: RequestStatus,
  ): Observable<[string, string, string, RequestStages]> {
    return this.http.post<[string, string, string, RequestStages]>(
      `${this.baseUrl}/next_step`,
      requestStatus,
    );
  }
}
