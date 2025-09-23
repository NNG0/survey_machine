import {
  AppState,
  Article,
  RawArticle,
  RequestStages,
  RequestStatus,
  StatusSetting,
  StepInformation,
  StepState,
} from "./models";

/*
const exampleResult: RawArticle = {
    title: 'Example Research Paper Title',
    abstract: 'This is an example abstract for a research paper. It provides a brief overview of the research conducted and the main findings.',
    url: 'https://doi.org/10.1000/example',
    author: 'John Doe, Jane Smith',
};

const initialArticle: Article = {
    article: exampleResult,
    problem_questions: null,
    methods: null
}
*/

const initialStatusSetting: StatusSetting = {
  research_question: "",
  paper_limit: 5, // Defaults to 5 in backend
  num_key_questions: 5,
};

export const initialRequestStatus: RequestStatus = {
  key_questions: [],
  // papers: [initialArticle],
  papers: [],
  draft: [],
  settings: initialStatusSetting,
};

const initialStepInformation: StepInformation = {
  warnings: [],
  errors: [],
};

export const orderedRequestStages: RequestStages[] = [
  RequestStages.CREATING_KEY_QUESTIONS,
  RequestStages.FINDING_LITERATURE,
  RequestStages.PARSE_PAPERS,
  RequestStages.ADJUST_KEY_QUESTIONS,
  RequestStages.EXTRACT_RELEVANT_RESULTS_FROM_PAPERS,
  RequestStages.CREATING_DRAFT_HEADINGS,
  RequestStages.FILLING_DRAFT_CONTENT,
  RequestStages.FINISHED
]

const initialStepState: StepState = {
  status: initialRequestStatus,
  step_information: initialStepInformation,
  stage: orderedRequestStages[0],
};

export const initialAppState: AppState = {
  current_step: initialStepState,
  history: [],
};
