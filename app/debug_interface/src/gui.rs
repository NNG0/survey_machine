use std::sync::mpsc::{Receiver, Sender};

use egui::{RichText, TextEdit};
use egui_commonmark::CommonMarkCache;
use log::info;
use rand::Rng;
use reqwest::blocking::Client;

use crate::types::{
    NextStepResponse, RawArticle, RequestStatus, RunNextStepResponse, get_testing_status,
};

pub fn run_gui() {
    let options = eframe::NativeOptions::default();
    eframe::run_native(
        "Survey Machine Debug Interface",
        options,
        Box::new(|_cc| Ok(Box::new(MyApp::new()))),
    )
    .expect("Failed to start eframe");
}

// For debug, we'll model an event as a string with a point in time that has a log level.
struct Event {
    timestamp: chrono::DateTime<chrono::Local>,
    level: log::Level,
    message: String,
}

// Enum list of possible open panels
enum AppPanel {
    Events,
    Status,
    MarkdownPreview,
}

struct MyApp {
    status: RequestStatus,
    stage: String,
    reqwest_client: reqwest::blocking::Client,
    events: Vec<Event>,
    current_panel: AppPanel,
    update_sender: Sender<Result<RunNextStepResponse, reqwest::Error>>,
    update_receiver: Receiver<Result<RunNextStepResponse, reqwest::Error>>,
    is_editable: bool, // Whether a step is currently being executed, disables editing
    markdown_cache: CommonMarkCache,
}

fn run_next_step(
    reqwest_client: &Client,
    status: &RequestStatus,
) -> Result<RunNextStepResponse, reqwest::Error> {
    let res = reqwest_client
        .post("http://localhost:8001/run_single_next_step")
        .json(status)
        .timeout(std::time::Duration::from_secs(300)) // 5 minute timeout, some steps can take a while
        .send()?;
    info!("Status: {}", res.status());
    res.json()
}

impl MyApp {
    fn new() -> Self {
        let (update_sender, update_receiver) = std::sync::mpsc::channel();
        Self {
            status: get_testing_status(),
            stage: "Initializing".to_string(),
            reqwest_client: reqwest::blocking::Client::new(),
            events: Vec::new(),
            current_panel: AppPanel::Status,
            update_sender,
            update_receiver,
            is_editable: true, // Initially editable
            markdown_cache: CommonMarkCache::default(),
        }
    }

    fn get_next_step(&self) -> Result<NextStepResponse, reqwest::Error> {
        let res = self
            .reqwest_client
            .post("http://localhost:8001/next_step")
            .json(&self.status)
            .send()?;
        info!("Status: {}", res.status());
        res.json()
    }

    fn get_next_step_and_update(&mut self) {
        match self.get_next_step() {
            Ok(next_step) => {
                self.stage = next_step.0.clone();
                self.events.push(Event {
                    timestamp: chrono::Local::now(),
                    level: log::Level::Info,
                    message: format!("Next step: {}", next_step.0),
                });
            }
            Err(e) => {
                self.events.push(Event {
                    timestamp: chrono::Local::now(),
                    level: log::Level::Error,
                    message: format!("Error getting next step: {e}"),
                });
            }
        }
    }

    fn execute_next_step(&mut self) {
        // Instead of blocking the UI, we spawn a thread to do this.
        let sender = self.update_sender.clone();
        let status_clone = self.status.clone();
        let client = self.reqwest_client.clone();
        std::thread::spawn(move || {
            // Run the next step, then send the result back to the main thread.
            let result = run_next_step(&client, &status_clone);
            sender.send(result).expect("Failed to send update");
        });
    }
}

impl eframe::App for MyApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // Selection Panel
        egui::TopBottomPanel::top("top_panel").show(ctx, |ui| {
            ui.horizontal_wrapped(|ui| {
                ui.heading("Survey Machine Debug Interface");
                if ui.button("Events").clicked() {
                    self.current_panel = AppPanel::Events;
                }
                if ui.button("Status").clicked() {
                    self.current_panel = AppPanel::Status;
                }
                if ui.button("Markdown Preview").clicked() {
                    self.current_panel = AppPanel::MarkdownPreview;
                }
            });
        });
        // Status Panel
        egui::TopBottomPanel::bottom("bottom_panel").show(ctx, |ui| {
            ui.horizontal_wrapped(|ui| {
                ui.label(format!("Current Stage: {}", self.stage));
                // Also add a spinner if the app is not editable (i.e., a step is being executed)
                if !self.is_editable {
                    ui.label("Executing step...");
                    ui.spinner();
                }
            });
        });
        // Main Panel
        egui::CentralPanel::default().show(ctx, |ui| match self.current_panel {
            AppPanel::Events => {
                ui.heading("Events");
                egui::ScrollArea::vertical().show(ui, |ui| {
                    for event in &self.events {
                        ui.horizontal(|ui| {
                            // Show a color based on log level
                            let color = match event.level {
                                log::Level::Error => egui::Color32::RED,
                                log::Level::Warn => egui::Color32::YELLOW,
                                log::Level::Info => egui::Color32::GREEN,
                                log::Level::Debug => egui::Color32::LIGHT_BLUE,
                                log::Level::Trace => egui::Color32::DARK_GRAY,
                            };
                            // ui.colored_label(
                            //     color,
                            //     format!("[{:?}] {}", event.timestamp, event.message),
                            // );
                            ui.label(
                                RichText::new(format!(
                                    "[{}] {}",
                                    event.timestamp.format("%Y-%m-%d %H:%M:%S"),
                                    event.message
                                ))
                                .color(color),
                            );
                        });
                    }
                });
            }
            AppPanel::MarkdownPreview => {
                // Render the draft, if it exists, as markdown
                ui.heading("Markdown Preview");
                if self.status.draft.is_empty() {
                    ui.label("No draft available yet.");
                } else {
                    let mut markdown_content = String::new();
                    for heading in &self.status.draft {
                        markdown_content.push_str(&format!("{}\n\n", heading.heading)); // The heads should include the # for markdown
                        if let Some(content) = &heading.content {
                            markdown_content.push_str(&format!("{content}\n\n"));
                        }
                    }
                    // Use egui_markdown to render the markdown content
                    // egui_markdown::MarkdownArea::new(&markdown_content).show(ui);
                    egui_commonmark::CommonMarkViewer::new().show(
                        ui,
                        &mut self.markdown_cache,
                        &markdown_content,
                    );
                }
            }
            AppPanel::Status => {
                ui.heading("Current Status");
                egui::ScrollArea::vertical().show(ui, |ui| {
                    self.status
                        .get_visualization(self.is_editable, ui, &mut self.events);
                });
                // Just the button to get information about the next step
                if ui.button("Get Next Step Information").clicked() && self.is_editable {
                    // Deduplicate click protection
                    self.is_editable = false;
                    self.get_next_step_and_update();
                    self.is_editable = true;
                }
                // The button that actually runs the next step
                if ui.button("Execute Next Step").clicked() {
                    self.is_editable = false;
                    self.execute_next_step();
                }

                if let Ok(result) = self.update_receiver.try_recv() {
                    self.is_editable = true;
                    match result {
                        Err(e) => {
                            self.events.push(Event {
                                timestamp: chrono::Local::now(),
                                level: log::Level::Error,
                                message: format!("Error getting next step: {e}"),
                            });
                        }
                        Ok(r) => {
                            self.status = r.0; // Updated status
                            for warning in &r.1.warnings {
                                self.events.push(Event {
                                    timestamp: chrono::Local::now(),
                                    level: log::Level::Warn,
                                    message: format!("Warning: {warning}"),
                                });
                            }
                            for error in &r.1.errors {
                                self.events.push(Event {
                                    timestamp: chrono::Local::now(),
                                    level: log::Level::Error,
                                    message: format!("Error: {error}"),
                                });
                            }
                        }
                    }
                    // Also update the next step information
                    self.get_next_step_and_update();
                    // ctx.request_repaint(); // Ensure the UI updates to reflect new status
                    // This can lead to a lot of updates, so we don't do it automatically.
                }
            }
        });
    }
}

impl RequestStatus {
    fn get_visualization(&mut self, is_editable: bool, ui: &mut egui::Ui, events: &mut Vec<Event>) {
        // The RequestStatus consists of:
        // - key_questions: Option<Vec<KeyQuestion>>
        // - papers: Vec<Article>
        // - draft: Vec<DraftHeading>
        // - settings: StatusSetting

        // In oder to be able to edit lists where each element could be edited, we would need to borrow the list mutably twice, which is not allowed.
        // To circumvent this, we'll store updates to the state here, collect them, and apply them after the UI code.
        let mut updates: Vec<Box<dyn FnOnce(&mut Self)>> = Vec::new();

        // We show these under each other in a vertical layout.
        ui.vertical(|ui| {
            // We can visualize all of these in a structured way, by using collapsible sections for each part.
            egui::CollapsingHeader::new("Key Questions")
                .default_open(true)
                .show(ui, |ui| {
                    if let Some(key_questions) = self.key_questions.as_mut() {
                        for (i, (question, related_methods, survey_result)) in
                            key_questions.iter_mut().enumerate()
                        {
                            ui.horizontal(|ui| {
                                ui.label(format!("{}. Question:", i + 1));
                                // Button to remove this question
                                if ui
                                    .button("❌")
                                    .on_hover_text("Remove this question")
                                    .clicked()
                                {
                                    updates.push(Box::new(move |status: &mut RequestStatus| {
                                        if let Some(questions) = status.key_questions.as_mut() {
                                            if i < questions.len() {
                                                questions.remove(i);
                                            }
                                        }
                                    }));
                                }
                            });
                            ui.add_enabled(
                                is_editable,
                                TextEdit::singleline(question).desired_width(f32::INFINITY),
                            );
                            if let Some(related_methods) = related_methods {
                                ui.label("   Related Methods:");
                                for (j, method) in related_methods.iter_mut().enumerate() {
                                    // Button to remove this method (from question i, at method j)
                                    if ui
                                        .button("❌")
                                        .on_hover_text("Remove this method")
                                        .clicked()
                                    {
                                        updates.push(Box::new(
                                            move |status: &mut RequestStatus| {
                                                if let Some(questions) =
                                                    status.key_questions.as_mut()
                                                {
                                                    if i < questions.len() {
                                                        if let Some(methods) =
                                                            questions[i].1.as_mut()
                                                        {
                                                            if j < methods.len() {
                                                                methods.remove(j);
                                                            }
                                                        }
                                                    }
                                                }
                                            },
                                        ));
                                    }
                                    ui.add_enabled(
                                        is_editable,
                                        TextEdit::singleline(method).desired_width(f32::INFINITY),
                                    );
                                }
                                // Button to add a new related method
                                if ui
                                    .button("Add Related Method")
                                    .on_hover_text("Add a new related method")
                                    .clicked()
                                {
                                    updates.push(Box::new(move |status: &mut RequestStatus| {
                                        if let Some(questions) = status.key_questions.as_mut() {
                                            if i < questions.len() {
                                                if let Some(methods) = questions[i].1.as_mut() {
                                                    methods.push(String::new());
                                                } else {
                                                    questions[i].1 = Some(vec![String::new()]);
                                                }
                                            }
                                        }
                                    }));
                                }
                            }
                            if let Some(result) = survey_result {
                                ui.label("   Survey Result:");
                                ui.add_enabled(
                                    is_editable,
                                    TextEdit::multiline(&mut result.result)
                                        .desired_width(f32::INFINITY),
                                );
                            }
                        }
                    } else {
                        ui.label("No key questions defined.");
                    }
                    // Button that adds a new empty key question
                    if ui
                        .button("Add Key Question")
                        .on_hover_text("Add a new key question")
                        .clicked()
                    {
                        updates.push(Box::new(|status: &mut RequestStatus| {
                            if let Some(questions) = status.key_questions.as_mut() {
                                questions.push((
                                    // question:
                                    String::new(),
                                    // related_methods:
                                    Some(Vec::new()),
                                    // survey_result:
                                    None,
                                ));
                            }
                        }));
                    }
                });
            egui::CollapsingHeader::new("Papers").show(ui, |ui| {
                for (i, paper) in self.papers.iter_mut().enumerate() {
                    // Title, Author, Abstract, URL
                    // ui.label(format!(
                    //     "Title: {}\nAuthor: {}\nAbstract: {}\nURL: {}\n---",
                    //     paper.article.title.as_deref().unwrap_or("No title"),
                    //     paper.article.author.as_deref().unwrap_or("No author"),
                    //     paper.article.abstract_.as_deref().unwrap_or("No abstract"),
                    //     paper.article.url.as_deref().unwrap_or("No URL")
                    // ));

                    // Button to remove this paper
                    ui.horizontal(|ui| {
                        ui.label("Paper:");
                        if ui.button("❌").on_hover_text("Remove this paper").clicked() {
                            updates.push(Box::new(move |status: &mut RequestStatus| {
                                if i < status.papers.len() {
                                    status.papers.remove(i);
                                }
                            }));
                        }
                    });

                    ui.label("Title:");
                    if let Some(title) = paper.article.title.as_mut() {
                        ui.add_enabled(
                            is_editable,
                            TextEdit::singleline(title).desired_width(f32::INFINITY),
                        );
                    } else {
                        ui.label("No title");
                        if is_editable {
                            // Button to turn empty title into editable title
                            if ui
                                .button("Add Title")
                                .on_hover_text("Add a title to this paper")
                                .clicked()
                            {
                                updates.push(Box::new(move |status: &mut RequestStatus| {
                                    if i < status.papers.len() {
                                        status.papers[i].article.title = Some(String::new());
                                    }
                                }));
                            }
                        }
                    }

                    ui.label("Author:");
                    if let Some(author) = paper.article.author.as_mut() {
                        ui.add_enabled(
                            is_editable,
                            TextEdit::singleline(author).desired_width(f32::INFINITY),
                        );
                    } else {
                        ui.label("No author");
                        if is_editable {
                            // Button to turn empty author into editable author
                            if ui
                                .button("Add Author")
                                .on_hover_text("Add an author to this paper")
                                .clicked()
                            {
                                updates.push(Box::new(move |status: &mut RequestStatus| {
                                    if i < status.papers.len() {
                                        status.papers[i].article.author = Some(String::new());
                                    }
                                }));
                            }
                        }
                    }

                    ui.label("Abstract:");
                    if let Some(abstract_) = paper.article.abstract_.as_mut() {
                        ui.add_enabled(
                            is_editable,
                            TextEdit::multiline(abstract_).desired_width(f32::INFINITY),
                        );
                    } else {
                        ui.label("No abstract");
                        if is_editable {
                            // Button to turn empty abstract into editable abstract
                            if ui
                                .button("Add Abstract")
                                .on_hover_text("Add an abstract to this paper")
                                .clicked()
                            {
                                updates.push(Box::new(move |status: &mut RequestStatus| {
                                    if i < status.papers.len() {
                                        status.papers[i].article.abstract_ = Some(String::new());
                                    }
                                }));
                            }
                        }
                    }

                    ui.label("URL:");
                    if let Some(url) = paper.article.url.as_mut() {
                        ui.add_enabled(
                            is_editable,
                            TextEdit::singleline(url).desired_width(f32::INFINITY),
                        );
                        // Button to open the URL in a browser
                        ui.hyperlink_to("Open URL", url);
                    } else {
                        ui.label("No URL");
                        if is_editable {
                            // Button to turn empty URL into editable URL
                            if ui
                                .button("Add URL")
                                .on_hover_text("Add a URL to this paper")
                                .clicked()
                            {
                                updates.push(Box::new(move |status: &mut RequestStatus| {
                                    if i < status.papers.len() {
                                        status.papers[i].article.url = Some(String::new());
                                    }
                                }));
                            }
                        }
                    }

                    // The other two (problem_questions, methods), we display as collapsed sections
                    egui::CollapsingHeader::new("Problem Questions")
                        .default_open(false)
                        .id_salt(i) // Ensure unique ID for each paper, the index i is fine
                        .show(ui, |ui| {
                            if let Some(questions) = paper.problem_questions.as_mut() {
                                for (j, q) in questions.iter_mut().enumerate() {
                                    // Button to remove this question (from paper i, at question j)
                                    ui.horizontal(|ui| {
                                        ui.label("Question:");
                                        if ui
                                            .button("❌")
                                            .on_hover_text("Remove this question")
                                            .clicked()
                                        {
                                            updates.push(Box::new(
                                                move |status: &mut RequestStatus| {
                                                    if i < status.papers.len() {
                                                        if let Some(questions) = status.papers[i]
                                                            .problem_questions
                                                            .as_mut()
                                                        {
                                                            if j < questions.len() {
                                                                questions.remove(j);
                                                            }
                                                        }
                                                    }
                                                },
                                            ));
                                        }
                                    });
                                    // ui.label(format!("- {q}"));
                                    ui.add_enabled(
                                        is_editable,
                                        TextEdit::singleline(q).desired_width(f32::INFINITY),
                                    );
                                }
                            }
                            // Button to add a new question
                            if ui
                                .button("Add Problem Question")
                                .on_hover_text("Add a new problem question")
                                .clicked()
                            {
                                updates.push(Box::new(move |status: &mut RequestStatus| {
                                    if i < status.papers.len() {
                                        if let Some(questions) =
                                            status.papers[i].problem_questions.as_mut()
                                        {
                                            questions.push(String::new());
                                        } else {
                                            status.papers[i].problem_questions =
                                                Some(vec![String::new()]);
                                        }
                                    }
                                }));
                            }
                        });
                    egui::CollapsingHeader::new("Methods")
                        .default_open(false)
                        .id_salt(i + 1000) // Ensure unique ID for each paper, the index i is fine, just offset by 1000 to avoid collision with above
                        .show(ui, |ui| {
                            if let Some(methods) = paper.methods.as_mut() {
                                for (j, m) in methods.iter_mut().enumerate() {
                                    // Also button to remove this method (from paper i, at method j)
                                    ui.horizontal(|ui| {
                                        ui.label("Method:");
                                        if ui
                                            .button("❌")
                                            .on_hover_text("Remove this method")
                                            .clicked()
                                        {
                                            updates.push(Box::new(
                                                move |status: &mut RequestStatus| {
                                                    if i < status.papers.len() {
                                                        if let Some(methods) =
                                                            status.papers[i].methods.as_mut()
                                                        {
                                                            if j < methods.len() {
                                                                methods.remove(j);
                                                            }
                                                        }
                                                    }
                                                },
                                            ));
                                        }
                                    });
                                    ui.add_enabled(
                                        is_editable,
                                        TextEdit::singleline(m).desired_width(f32::INFINITY),
                                    );
                                }
                            }
                            // Button to add a new method
                            if ui
                                .button("Add Method")
                                .on_hover_text("Add a new method")
                                .clicked()
                            {
                                updates.push(Box::new(move |status: &mut RequestStatus| {
                                    if i < status.papers.len() {
                                        if let Some(methods) = status.papers[i].methods.as_mut() {
                                            methods.push(String::new());
                                        } else {
                                            status.papers[i].methods = Some(vec![String::new()]);
                                        }
                                    }
                                }));
                            }
                        });
                }
                // Button that adds a new empty paper
                if ui
                    .button("Add Paper")
                    .on_hover_text("Add a new paper")
                    .clicked()
                {
                    updates.push(Box::new(|status: &mut RequestStatus| {
                        status.papers.push(crate::types::Article {
                            problem_questions: None,
                            methods: None,
                            article: RawArticle {
                                id: rand::rng()
                                    .sample_iter(&rand::distr::Alphanumeric)
                                    .take(20)
                                    .map(char::from)
                                    .collect(),
                                title: None,
                                author: None,
                                abstract_: None,
                                saved_at: None,
                                url: None,
                                doi: None,
                            },
                        });
                    }));
                }
            });
            egui::CollapsingHeader::new("Draft").show(ui, |ui| {
                for (i, heading) in self.draft.iter_mut().enumerate() {
                    // ui.label("Heading:");
                    // Button to remove this heading
                    ui.horizontal(|ui| {
                        ui.label(format!("Heading {}:", i + 1));
                        if ui
                            .button("❌")
                            .on_hover_text("Remove this heading")
                            .clicked()
                        {
                            updates.push(Box::new(move |status: &mut RequestStatus| {
                                if i < status.draft.len() {
                                    status.draft.remove(i);
                                }
                            }));
                        }
                    });
                    ui.add_enabled(
                        is_editable,
                        TextEdit::singleline(&mut heading.heading).desired_width(f32::INFINITY),
                    );
                    // ui.label("Content:");
                    if let Some(content) = heading.content.as_mut() {
                        ui.add_enabled(
                            is_editable,
                            TextEdit::multiline(content).desired_width(f32::INFINITY),
                        );
                    } else {
                        ui.label("No content");
                        // Button to turn empty content into editable content
                        if ui
                            .button("Add Content")
                            .on_hover_text("Add content to this heading")
                            .clicked()
                        {
                            updates.push(Box::new(move |status: &mut RequestStatus| {
                                if i < status.draft.len() {
                                    status.draft[i].content = Some(String::new());
                                }
                            }));
                        }
                    }
                }
                // Button that adds a new empty heading
                if ui
                    .button("Add Heading")
                    .on_hover_text("Add a new heading")
                    .clicked()
                {
                    updates.push(Box::new(|status: &mut RequestStatus| {
                        status.draft.push(crate::types::DraftHeading {
                            heading: String::new(),
                            content: None,
                        })
                    }))
                };
            });
            egui::CollapsingHeader::new("Settings")
                .default_open(false)
                .show(ui, |ui| {
                    ui.label("Research Question:");
                    ui.add_enabled(
                        is_editable,
                        TextEdit::singleline(&mut self.settings.research_question)
                            .desired_width(f32::INFINITY),
                    );
                    ui.add_enabled(
                        is_editable,
                        egui::Slider::new(&mut self.settings.paper_limit, 1..=10)
                            .text("Paper Limit"),
                    );
                    ui.add_enabled(
                        is_editable,
                        egui::Slider::new(&mut self.settings.num_key_questions, 1..=10)
                            .text("Number of Key Questions"),
                    );
                });
        });

        // Apply all updates, but only if editable
        if is_editable {
            for update in updates {
                update(self);
            }
        } else {
            // If not editable, we discard the updates
            // (This should not happen, but just in case)
            events.push(Event {
                timestamp: chrono::Local::now(),
                level: log::Level::Warn,
                message: "Discarded updates while not editable".to_string(),
            });
        }
    }
}
