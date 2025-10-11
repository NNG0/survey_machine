import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { Observable } from "rxjs";
import { OpenAltexResponse, RequestStages, RequestStatus, StepInformation } from "../types/models";

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
    uploadForWorkflow(file: File, requestStatus: RequestStatus, workflowId?: string | null): Observable<any> {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('request_status_json', JSON.stringify(requestStatus));
        if (workflowId) {
          formData.append('workflow_id', workflowId);
        }

        return this.http.post(`${this.baseUrl}/upload_for_workflow`, formData);
      }

      getAllPapers(): Observable<any[]> {
        return this.http.get<any[]>(`${this.baseUrl}/papers`);
      }

      createWorkflowStatus(requestStatus: RequestStatus): Observable<any> {
        return this.http.post(`${this.baseUrl}/workflow_results`, requestStatus);
      }

      updateWorkflowStatus(workflowId: string, requestStatus: RequestStatus): Observable<any> {
        return this.http.put(`${this.baseUrl}/workflow_results/${workflowId}`, requestStatus);
      }

      getLatestWorkflowStatus(): Observable<any> {
        return this.http.get(`${this.baseUrl}/workflow_results/latest`);
      }

  searchOpenAlex(query: string): Observable<OpenAltexResponse> {
    return this.http.get<OpenAltexResponse>(
      `${this.baseUrl}/search_openalex?q=${encodeURIComponent(query)}`,
    );
  }
}
