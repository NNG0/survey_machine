import {
  AppState,
  RequestStages,
  RequestStatus,
  StatusSetting,
  StepInformation,
  StepState,
} from "./models";

const initialStatusSetting: StatusSetting = {
  research_question: "",
  paper_limit: 5, // Defaults to 5 in backend
  num_key_questions: 5,
};

export const initialRequestStatus: RequestStatus = {
  key_questions: [],
  papers: [],
  draft: [],
  settings: initialStatusSetting,
};

const initialStepInformation: StepInformation = {
  warnings: [],
  errors: [],
};

const initialStepState: StepState = {
  status: initialRequestStatus,
  step_information: initialStepInformation,
  // stage: RequestStages.CREATING_KEY_QUESTIONS,
};

export const initialAppState: AppState = {
  current_step: initialStepState,
  history: [],
};
