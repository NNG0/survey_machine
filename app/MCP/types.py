from enum import Enum
from typing import Self

from mcp_agent.workflows.llm.augmented_llm import AugmentedLLM

from pydantic import BaseModel, Field


class RawArticle(BaseModel):
    title: str | None
    author: str | None
    abstract: str | None
    url: str | None


class Article(BaseModel):
    article: RawArticle
    # key_findings: list[str] | None
    problem_questions: list[str] | None
    methods: list[str] | None
    relevance_score: float | None = None


class SurveyResult(BaseModel):
    result: str  # The result of a paper, shortly summarized
    # paper_url: str  # The URL of the paper the result is based on
    # The URLs are now part of the question.


class StatusSetting(BaseModel):
    research_question: str  # The research question for which the survey is created.
    paper_limit: int = (
        5  # The maximum number of papers to use for the survey. Defaults to 5.
    )
    num_key_questions: int = (
        5  # The number of key questions that are generated. Defaults to 5.
    )


class DraftHeading(BaseModel):
    title: str  # The title of the heading, together with the hashtags to denote the markdown Header level e.g. "# Introduction"
    content: str | None  # The content of the heading, in markdown format.


type KeyQuestion = tuple[str, list[str] | None, SurveyResult | None]


class RequestStatus(BaseModel):
    """This class is used to track the status of a single request over the lifetime of the server.
    It stores all data needed to track the request and is meant to represent the progress.
    It can also be stored and loaded due to this."""

    key_questions: list[KeyQuestion] | None = Field(
        default_factory=list
    )  # Each question may or may not be assigned a url to one or more papers.

    papers: list[Article] = Field(default_factory=list)  # The list of papers

    draft: list[DraftHeading] = Field(
        default_factory=list
    )  # The draft headings for the final document

    settings: StatusSetting  # The settings for the request, such as the research question and paper limit.
    # Does not change over the lifetime of the request.

    # The tracefile isn't used anymore. Instead, the history is stored in a database outside of the MCP module.

    def __init__(
        self,
        key_questions: list[tuple[str, list[str] | None, SurveyResult | None]]
        | None = Field(default_factory=list),  # TODO: is this right?
        papers: list[Article] = Field(default_factory=list),
        draft: list[DraftHeading] = Field(default_factory=list),
        settings: StatusSetting | None = None,
    ):
        """Initializes the RequestStatus object.
        If trace_file is given, the status will be saved to that file.
        """
        super().__init__(
            key_questions=key_questions,
            papers=papers,
            settings=settings,
            draft=draft,
        )

    def pretty_print(self):
        """Prints the status of the request in a human-readable format."""
        print(
            f"""
Request status:
        Settings:
                Research question: {self.settings.research_question}
                Paper limit: {self.settings.paper_limit}
                Target number of key questions: {self.settings.num_key_questions}
        Key questions:
                {"\n\t\t".join([f"Question: {question[0]}\n\t\t\tSources: {', '.join(question[1]) if question[1] else 'None'}\n\t\t\tResult: {question[2].result if question[2] else 'None'}" for question in self.key_questions] if self.key_questions else ["None"])}
        Papers:
                {"\n\t\t".join([f"Name: {paper.article.title}\n\t\t\tQuestions: {paper.problem_questions}\n\t\t\tMethods: {paper.methods}" for paper in self.papers])}
        Draft:
                {"\n\t\t".join([f"Title: {heading.title}\n\t\t\tContent: {heading.content}" for heading in self.draft])}
            """
        )  # TODO: Add a better pretty print function

    def to_dict(self) -> dict:
        """Returns the status as a dictionary."""
        # return self.__dict__ # This only bubbles up the JSON serialization problem.
        return self.model_dump()

    # I removed the setattr and gettrace methods stuff, because that was a gigantic hack to get the trace file to work.
    # Now it can be done manually in a much cleaner way.


class StepInformation(BaseModel):
    """This class is used to store information about what went wrong in a step of the agent workflow."""

    warnings: list[str] = Field(
        default_factory=list
    )  # Warnings that were raised during the step.
    errors: list[str] = Field(
        default_factory=list
    )  # Errors that were raised during the step.

    def add_warning(self, warning: str):
        """Adds a warning to the step information."""
        self.warnings.append(warning)

    def add_error(self, error: str):
        """Adds an error to the step information."""
        self.errors.append(error)

    def __init__(
        self, warnings: list[str] | None = None, errors: list[str] | None = None
    ):
        """Initializes the StepInformation object."""
        init_warnings = warnings if warnings is not None else []
        init_errors = errors if errors is not None else []
        super().__init__(warnings=init_warnings, errors=init_errors)

    def merge(self, other: Self):
        """Merges another StepInformation object into this one."""
        self.warnings.extend(other.warnings)
        self.errors.extend(other.errors)

    def print_warnings_and_errors(self):
        """Prints the step warnings and errors in a human-readable format."""
        if self.warnings:
            print("Warnings:")
            for warning in self.warnings:
                print(f"- {warning}")
        if self.errors:
            print("Errors:")
            for error in self.errors:
                print(f"- {error}")


class RequestStages(Enum):
    """An enum that represents the stages of a request."""

    # Note: These values are used to determine the order of the steps, so they should be unique and in ascending order.
    # However, they should not be used directly, only ever over the enum.
    CREATING_KEY_QUESTIONS = 50
    FINDING_LITERATURE = 100
    PARSE_PAPERS = 200
    ADJUST_KEY_QUESTIONS = 300
    EXTRACT_RELEVANT_RESULTS_FROM_PAPERS = 500
    CREATING_DRAFT_HEADINGS = 600
    FILLING_DRAFT_CONTENT = 700
    FINISHED = 999


class SupportedProviders(object):
    """An abstract class to express the different providers and models that are supported by the backend."""

    # The library only needs a single function, which gives back an object representing the provider.
    def get_provider(self, agent=None) -> AugmentedLLM:
        """Returns an object representing the provider."""
        raise NotImplementedError("This method should be implemented by the subclass.")


class Ollama(SupportedProviders):
    """A class that represents the Ollama provider. Can specify a custom model."""

    model: str = "qwen3"  # Default model to use if none is specified.

    def __init__(self, model: str = "qwen"):
        """Initializes the Ollama provider with a specific model."""
        self.model = model

    def get_provider(self, agent=None) -> AugmentedLLM:
        """Returns an Ollama provider with the specified model."""
        from mcp_agent.workflows.llm.augmented_llm_ollama import OllamaAugmentedLLM

        if agent:
            # If an agent is provided, pass it to the OllamaAugmentedLLM
            return OllamaAugmentedLLM(default_model=self.model, agent=agent)
        return OllamaAugmentedLLM(default_model=self.model)


class OpenRouter(SupportedProviders):
    """A class that represents the OpenRouter provider. It uses the OpenAI Provider, so the API key in the secrets file needs to be set on the OpenAI provider."""

    def get_provider(self, agent=None) -> AugmentedLLM:
        """Returns an OpenRouter provider."""
        from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

        if agent:
            # If an agent is provided, pass it to the OpenAIAugmentedLLM
            return OpenAIAugmentedLLM(
                agent=agent, base_url="https://api.openrouter.ai/v1"
            )
        return OpenAIAugmentedLLM()
