use egui::RichText;
use log::info;

use crate::types::{NextStepResponse, RequestStatus, get_testing_status};

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
    timestamp: std::time::SystemTime,
    level: log::Level,
    message: String,
}

// Enum list of possible open panels
enum AppPanel {
    Events,
    Status,
}

struct MyApp {
    status: RequestStatus,
    reqwest_client: reqwest::blocking::Client,
    events: Vec<Event>,
    current_panel: AppPanel,
}
impl MyApp {
    fn new() -> Self {
        Self {
            status: get_testing_status(),
            reqwest_client: reqwest::blocking::Client::new(),
            events: Vec::new(),
            current_panel: AppPanel::Status,
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
}

impl eframe::App for MyApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        egui::TopBottomPanel::top("top_panel").show(ctx, |ui| {
            ui.horizontal_wrapped(|ui| {
                ui.heading("Survey Machine Debug Interface");
                if ui.button("Events").clicked() {
                    self.current_panel = AppPanel::Events;
                }
                if ui.button("Status").clicked() {
                    self.current_panel = AppPanel::Status;
                }
            });
        });
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
                                RichText::new(format!("[{:?}] {}", event.timestamp, event.message))
                                    .color(color),
                            );
                        });
                    }
                });
            }
            AppPanel::Status => {
                ui.heading("Current Status");
                egui::ScrollArea::vertical().show(ui, |ui| {
                    self.status.get_visualization(ui);
                });
                if ui.button("Get Next Step").clicked() {
                    match self.get_next_step() {
                        Ok(next_step) => {
                            self.events.push(Event {
                                timestamp: std::time::SystemTime::now(),
                                level: log::Level::Info,
                                message: format!("Next step: {}", next_step.0),
                            });
                        }
                        Err(e) => {
                            self.events.push(Event {
                                timestamp: std::time::SystemTime::now(),
                                level: log::Level::Error,
                                message: format!("Error getting next step: {e}"),
                            });
                        }
                    }
                }
            }
        });
    }
}

impl RequestStatus {
    fn get_visualization(&self, ui: &mut egui::Ui) {
        // The RequestStatus consists of:
        // - key_questions: Option<Vec<KeyQuestion>>
        // - papers: Vec<Article>
        // - draft: Vec<DraftHeading>
        // - settings: StatusSetting

        // We show these next to each other in a vertical layout.
        ui.horizontal(|ui| {
            // We can visualize all of these in a structured way, by using collapsible sections for each part.
            egui::CollapsingHeader::new("Key Questions")
                .default_open(true)
                .show(ui, |ui| {
                    if let Some(key_questions) = &self.key_questions {
                        for (i, (question, related_methods, survey_result)) in
                            key_questions.iter().enumerate()
                        {
                            ui.label(format!("{}. {}", i + 1, question));
                            if let Some(methods) = related_methods {
                                ui.label(format!("   Related Methods: {methods:?}"));
                            }
                            if let Some(result) = survey_result {
                                ui.label(format!("   Survey Result: {}", result.result));
                            }
                        }
                    } else {
                        ui.label("No key questions defined.");
                    }
                });
            egui::CollapsingHeader::new("Papers").show(ui, |ui| {
                for paper in &self.papers {
                    // Title, Author, Abstract, URL
                    ui.label(format!(
                        "Title: {}\nAuthor: {}\nAbstract: {}\nURL: {}\n---",
                        paper.article.title.as_deref().unwrap_or("No title"),
                        paper.article.author.as_deref().unwrap_or("No author"),
                        paper.article.abstract_.as_deref().unwrap_or("No abstract"),
                        paper.article.url.as_deref().unwrap_or("No URL")
                    ));

                    // The other two (problem_questions, methods), we display as collapsed sections
                    egui::CollapsingHeader::new("Problem Questions")
                        .default_open(false)
                        .show(ui, |ui| {
                            if let Some(questions) = &paper.problem_questions {
                                for q in questions {
                                    ui.label(format!("- {q}"));
                                }
                            }
                        });
                    egui::CollapsingHeader::new("Methods")
                        .default_open(false)
                        .show(ui, |ui| {
                            if let Some(methods) = &paper.methods {
                                for m in methods {
                                    ui.label(format!("- {m}"));
                                }
                            }
                        });
                }
            });
            egui::CollapsingHeader::new("Draft").show(ui, |ui| {
                for heading in &self.draft {
                    ui.label(format!("Heading: {}", heading.heading));
                    if let Some(content) = &heading.content {
                        ui.label(format!("Content: {content}"));
                    }
                }
            });
            egui::CollapsingHeader::new("Settings")
                .default_open(false)
                .show(ui, |ui| {
                    ui.label(format!(
                        "Research Question: {}",
                        self.settings.research_question
                    ));
                    ui.label(format!("Paper Limit: {}", self.settings.paper_limit));
                    ui.label(format!(
                        "Number of Key Questions: {}",
                        self.settings.num_key_questions
                    ));
                });
        });
    }
}
