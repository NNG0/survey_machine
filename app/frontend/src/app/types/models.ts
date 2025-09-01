export interface RawArticle {
  title: string | null;
  author: string | null;
  abstract: string | null;
  url: string | null;
}

export interface Article {
  article: RawArticle;
  problem_questions: string[] | null;
  methods: string[] | null;
}

export interface SurveyResult {
  result: string;
}

export interface StatusSetting {
  research_question: string;
  paper_limit: number; // Defaults to 5 in backend
  num_key_questions: number; // Defaults to 5 in backend
}

export interface RequestStatus {
  key_questions: [string, string[] | null, SurveyResult | null][];
  papers: [Article, number | null][];
  results: SurveyResult[];
  settings: StatusSetting;
}

export interface StepInformation {
  warnings: string[];
  errors: string[];
}

export enum RequestStages {
  CREATING_KEY_QUESTIONS = 50,
  FINDING_LITERATURE = 100,
  PARSE_PAPERS = 200,
  ADJUST_KEY_QUESTIONS = 300,
  EXTRACT_RELEVANT_RESULTS_FROM_PAPERS = 500,
  FINISHED = 999,
}
