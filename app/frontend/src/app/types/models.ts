export interface RawArticle {
  id: string;
  title: string | null;
  author: string | null;
  savedAt: string | null;
  abstract: string | null;
  url: string | null;
  doi: string | null;
}

export interface Article {
  article: RawArticle;
  problem_questions: string[] | null;
  methods: string[] | null;
  relevance_score?: number;
}
export interface DraftHeading {
  title: string;
  content: string | null;
}

// Note: Due to how interfaces are handled in TypeScript's type system (It's Just A Dict),
// the DraftItem interface can be used in place of the DraftHeading. This is why it extends DraftHeading.
// On the python side, the DraftItem is read as a dict with extra fields, which are simply ignored.
export interface DraftItem extends DraftHeading {
  id: string;
  title: string;
  createdAt: string; // ISO string
  updatedAt: string; // ISO string
  keywords?: string[];
  markdown?: string;
  content: string | null;
}

export interface SurveyResult {
  result: string;
}

export interface StatusSetting {
  research_question: string;
  paper_limit: number; // Defaults to 5 in backend
  num_key_questions: number; // Defaults to 5 in backend
}

export type KeyQuestion = [string, string[] | null, SurveyResult | null];

export interface RequestStatus {
  key_questions: [string, string[] | null, SurveyResult | null][] | null;
  papers: Article[];
  draft: DraftItem[];
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
  CREATING_DRAFT_HEADINGS = 600,
  FILLING_DRAFT_CONTENT = 700,
  FINISHED = 999,
}

export interface HistoryEntry {
  id: number;
  state: StepState;
}

export interface StepState {
  status: RequestStatus;
  step_information: StepInformation;
  stage: RequestStages;
  saved_papers: Article[];
  literature_search_results: Article[];
}

export interface AppState {
  current_step: StepState;
  history: HistoryEntry[];
}

export interface OpenAlexResult {
  id: string;
  title: string;
  abstract: string;
  authors: string[];
  published_date: string | null;
  fcwi: number;
  open_access: any;
  cited_by_count: number;
  primary_topic: string;
  subfield: any;
  pdf_url: string | null;
}

export interface OpenAltexResponse {
  query: string;
  results: OpenAlexResult[];
}