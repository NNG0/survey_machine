use serde::{Deserialize, Serialize};
use serde_repr::{Deserialize_repr, Serialize_repr};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct RawArticle {
    pub title: Option<String>,
    pub author: Option<String>,
    #[serde(rename = "abstract")]
    pub abstract_: Option<String>,
    pub url: Option<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Article {
    pub article: RawArticle,
    pub problem_questions: Option<Vec<String>>,
    pub methods: Option<Vec<String>>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct SurveyResult {
    pub result: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct StatusSetting {
    pub research_question: String,
    pub paper_limit: i32, // Should technically be u32, but if something weird happens in the database, this shouldn't just fail.
    pub num_key_questions: i32,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct DraftHeading {
    pub heading: String,
    pub content: Option<String>,
}

pub type KeyQuestion = (String, Option<Vec<String>>, Option<SurveyResult>); // (question, related methods, survey result)
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct RequestStatus {
    pub key_questions: Option<Vec<KeyQuestion>>,
    pub papers: Vec<Article>,
    pub draft: Vec<DraftHeading>,
    pub settings: StatusSetting,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct StepInformation {
    pub warnings: Vec<String>,
    pub errors: Vec<String>,
}

#[derive(Serialize_repr, Deserialize_repr, Debug)]
#[repr(i32)]
pub enum RequestStages {
    CREATING_KEY_QUESTIONS = 50,
    FINDING_LITERATURE = 100,
    PARSE_PAPERS = 200,
    ADJUST_KEY_QUESTIONS = 300,
    EXTRACT_RELEVANT_RESULTS_FROM_PAPERS = 500,
    CREATING_DRAFT_HEADINGS = 600,
    FILLING_DRAFT_CONTENT = 700,
    FINISHED = 999,
}

pub type NextStepResponse = (String, String, String, RequestStages); // Human message, function name to call for single next step, function name for all remaining steps of this stage, current stage

#[derive(Serialize, Deserialize, Debug)]
pub struct RunNextStepResponse(pub RequestStatus, pub StepInformation); // Updated status, information about the step

pub fn get_testing_settings() -> StatusSetting {
    StatusSetting {
        research_question: "Which sorting algorithms are used in practice, from standard libraries to personal projects?".to_string(),
        paper_limit: 2,
        num_key_questions: 2,
    }
}

pub fn get_testing_status() -> RequestStatus {
    RequestStatus {
        settings: get_testing_settings(),
        papers: vec![],
        key_questions: Some(vec![]),
        draft: vec![],
    }
}
