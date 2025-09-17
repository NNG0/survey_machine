use serde::{Deserialize, Serialize};
use serde_repr::{Deserialize_repr, Serialize_repr};
fn main() {
    // Create the initial testing status
    let mut status = get_testing_status();

    // The server runs on port 8001 of localhost, ask it for the status by querying /next_step with the current status as JSON
    let client = reqwest::blocking::Client::new();
    let res = client
        .post("http://localhost:8001/next_step")
        .json(&status)
        .send()
        .unwrap();

    println!("Status: {}", res.status());

    // Try to get a NextStepResponse from the server
    // let raw_text = res.text().unwrap();
    // println!("Raw text: {raw_text:?}");
    let mut next_step: Result<NextStepResponse, reqwest::Error> = res.json();
    while let Ok(ref next) = next_step
        && !matches!(next.3, RequestStages::FINISHED)
    {
        println!("Next step: {}", next.0); // Human message

        // The result contains the function name to call for the next step
        // let function_name = &next.1;

        // But to adhere to the python example, we will just keep calling /run_single_next_step
        let result: Result<RunNextStepResponse, reqwest::Error> = client
            .post("http://localhost:8001/run_single_next_step")
            .json(&status)
            .timeout(std::time::Duration::from_secs(300)) // 5 minute timeout, some steps can take a while
            .send()
            .inspect_err(|e| println!("Error sending request: {e}"))
            .and_then(|r| r.json());

        match result {
            Err(e) => {
                println!("Error getting next step: {e}");
                break;
            }
            Ok(r) => {
                status = r.0; // Updated status
                println!("Updated status: {status:#?}");
                for warning in &r.1.warnings {
                    println!("Warning: {warning}");
                }
                for error in &r.1.errors {
                    println!("Error: {error}");
                }

                // Also do client side rate limit honouring, just like in python.
                let rate_limit_hit = {
                    let mut hit = false;
                    for error in &r.1.errors {
                        if error.contains("Rate limit") {
                            hit = true;
                            break;
                        }
                    }
                    hit
                };
                if rate_limit_hit {
                    println!("Rate limit hit, waiting 60 seconds...");
                    std::thread::sleep(std::time::Duration::from_secs(60));
                } else {
                    // Wait a bit to avoid spamming the server too much
                    std::thread::sleep(std::time::Duration::from_secs(2));
                }

                // If it worked, get the next step.
                next_step = client
                    .post("http://localhost:8001/next_step")
                    .json(&status)
                    .send()
                    .inspect_err(|e| println!("Error sending request: {e}"))
                    .and_then(|r| r.json());
            }
        }
    }
    println!("Finished with status: {status:#?}");
    println!("Last next step response: {next_step:?}");
}

// Types from python

#[derive(Serialize, Deserialize, Debug)]
struct RawArticle {
    title: Option<String>,
    author: Option<String>,
    #[serde(rename = "abstract")]
    abstract_: Option<String>,
    url: Option<String>,
}

#[derive(Serialize, Deserialize, Debug)]
struct Article {
    article: RawArticle,
    problem_questions: Option<Vec<String>>,
    methods: Option<Vec<String>>,
}

#[derive(Serialize, Deserialize, Debug)]
struct SurveyResult {
    result: String,
}

#[derive(Serialize, Deserialize, Debug)]
struct StatusSetting {
    research_question: String,
    paper_limit: i32, // Should technically be u32, but if something weird happens in the database, this shouldn't just fail.
    num_key_questions: i32,
}

#[derive(Serialize, Deserialize, Debug)]
struct DraftHeading {
    heading: String,
    content: Option<String>,
}

type KeyQuestion = (String, Option<Vec<String>>, Option<SurveyResult>); // (question, related methods, survey result)
#[derive(Serialize, Deserialize, Debug)]
struct RequestStatus {
    key_questions: Option<Vec<KeyQuestion>>,
    papers: Vec<Article>,
    draft: Vec<DraftHeading>,
    settings: StatusSetting,
}

#[derive(Serialize, Deserialize, Debug)]
struct StepInformation {
    warnings: Vec<String>,
    errors: Vec<String>,
}

#[derive(Serialize_repr, Deserialize_repr, Debug)]
#[repr(i32)]
enum RequestStages {
    CREATING_KEY_QUESTIONS = 50,
    FINDING_LITERATURE = 100,
    PARSE_PAPERS = 200,
    ADJUST_KEY_QUESTIONS = 300,
    EXTRACT_RELEVANT_RESULTS_FROM_PAPERS = 500,
    CREATING_DRAFT_HEADINGS = 600,
    FILLING_DRAFT_CONTENT = 700,
    FINISHED = 999,
}

type NextStepResponse = (String, String, String, RequestStages); // Human message, function name to call for single next step, function name for all remaining steps of this stage, current stage

#[derive(Serialize, Deserialize, Debug)]
struct RunNextStepResponse(RequestStatus, StepInformation); // Updated status, information about the step

fn get_testing_settings() -> StatusSetting {
    StatusSetting {
        research_question: "Which sorting algorithms are used in practice, from standard libraries to personal projects?".to_string(),
        paper_limit: 2,
        num_key_questions: 2,
    }
}

fn get_testing_status() -> RequestStatus {
    RequestStatus {
        settings: get_testing_settings(),
        papers: vec![],
        key_questions: Some(vec![]),
        draft: vec![],
    }
}
