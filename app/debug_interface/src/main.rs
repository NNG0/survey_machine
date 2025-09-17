use crate::types::{NextStepResponse, RequestStages, RunNextStepResponse, get_testing_status};

mod gui;
mod types;

fn main() {
    env_logger::init();
    // test_standard_run();
    gui::run_gui();
}

fn test_standard_run() {
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
