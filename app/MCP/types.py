import asyncio
from enum import Enum
import time
from typing import Awaitable, Callable, Literal, Optional, Self, TypeVar

from pydantic import BaseModel, Field


# Try to get it to create an article
class Article(BaseModel):
    title: str | None
    author: str | None
    abstract: str | None
    url: str | None


class SurveyQuestion(BaseModel):
    question: str
    answer_type: (
        (
            Literal["Text"]
            | Literal["Multiple choice"]
            | Literal["Yes/No"]
            | Literal["Range"]
        )
        | None
    )  # The type of answer the questioned person can give. For example, "text", "multiple choice", "yes/no" or a "out of a range from x to y...". # TODO: Add more types of answers?
    options: (
        (list[str] | tuple[int, int] | Literal["Text field"]) | None
    )  # The options for the answer, if applicable. For example, ["yes", "no"] for a yes/no question.


class StatusSetting(BaseModel):
    research_question: str  # The research question for which the survey is created.
    paper_limit: int = (
        5  # The maximum number of papers to use for the survey. Defaults to 5.
    )
    question_per_article: int = (
        3  # The number of questions to create per article. Defaults to 3.
    )


class RequestStatus(BaseModel):
    """This class is used to track the status of a single request over the lifetime of the server.
    It stores all data needed to track the request and is meant to represent the progress.
    It can also be stored and loaded due to this."""

    papers: list[tuple[Article, float | None]] = Field(
        default_factory=list
    )  # The list of papers and their relevance scores

    questions: list[tuple[SurveyQuestion, float | None]] = Field(
        default_factory=list
    )  # The list of questions and their relevance scores

    settings: StatusSetting  # The settings for the request, such as the research question and paper limit.
    # Does not change over the lifetime of the request.

    trace_file: Optional[str] = Field(
        default=None, alias="__trace_file__"
    )  # The file to which the status is saved. If None, it is not saved to a file.
    # Any time the status is updated, a new line with the updated status is written to the file.
    # In Python, holding a file handle is not recommended, so we will open and close the file each time we write to it.

    def __init__(
        self,
        research_question: str,
        paper_limit: int | None = None,
        trace_file: str | None = None,
    ):
        """Initializes the RequestStatus object.
        If trace_file is given, the status will be saved to that file.
        """
        settings = StatusSetting(
            research_question=research_question, paper_limit=paper_limit or 5
        )
        super().__init__(
            papers=[],
            questions=[],
            settings=settings,
            trace_file=trace_file
        )

    def pretty_print(self):
        """Prints the status of the request in a human-readable format."""
        print(
            f"Request status: {self.model_dump()}"
        )  # TODO: Add a better pretty print function

    # I removed the setattr and gettrace methods stuff, because that was a gigantic hack to get the trace file to work.
    # Now it can be done manually in a much cleaner way.


class StepInformation(BaseModel):
    """This class is used to store information about what went wrong in a step of the agent workflow."""

    warnings: list[str] = Field(default_factory=list)  # Warnings that were raised during the step.
    errors: list[str] = Field(default_factory=list)  # Errors that were raised during the step.

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
    FINDING_LITERATURE = 100
    CHECKING_LITERATURE_RELEVANCE = 200
    CREATING_SURVEY_QUESTIONS = 300
    CHECKING_QUESTION_RELEVANCE = 400
    FORMATTING_SURVEY_QUESTIONS = 500
    FINISHED = 999
