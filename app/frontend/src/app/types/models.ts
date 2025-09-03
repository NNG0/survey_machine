export interface Article {
  title: string | null;
  author: string | null;
  abstract: string | null;
  url: string | null;
}

export type AnswerType = "Text" | "Multiple choice" | "Yes/No" | "Range";

export interface SurveyQuestion {
  question: string;
  answer_type?: AnswerType;
  options?: string[] | [number, number] | "Text field";
}

export interface StatusSetting {
  research_question: string;
  paper_limit: number;          // Defaults to 5 in Python
  question_per_article: number; // Defaults to 3 in Python
}

export interface RequestStatus {
  papers: [Article, number | null][];  // Changed from number to match Python's float | None
  questions: [SurveyQuestion, number | null][];  // Changed from number to match Python's float | None
  settings: StatusSetting;
  trace_file?: string;
}

export interface StepInformation {
  warnings: string[];
  errors: string[];
}

export enum RequestStages {
  FINDING_LITERATURE = 100,
  CHECKING_LITERATURE_RELEVANCE = 200,
  CREATING_SURVEY_QUESTIONS = 300,
  CHECKING_QUESTION_RELEVANCE = 400,
  FORMATTING_SURVEY_QUESTIONS = 500,
  FINISHED = 999
}

  
  

  
