import asyncio
import time
from typing import Awaitable, Callable, Literal, Optional, TypeVar

from pydantic import BaseModel


# Try to get it to create an article
class Article(BaseModel):
    title: str | None
    author: str | None
    abstract: str | None
    url: str | None


class SurveyQuestion(BaseModel):
    question: str
    answer_type: Literal["Text"] | Literal["Multiple choice"] | Literal["Yes/No"] | Literal["Range"] # The type of answer the questioned person can give. For example, "text", "multiple choice", "yes/no" or a "out of a range from x to y...". # TODO: Add more types of answers?
    options: list[str] | tuple[int, int] | Literal["Text field"] # The options for the answer, if applicable. For example, ["yes", "no"] for a yes/no question.
    

class RequestStatus:
    """This class is used to track the status of a single request over the lifetime of the server.
    It stores all data needed to track the request and is meant to represent the progress.
    It can also be stored and loaded due to this."""

    papers: list[tuple[Article, float | None]] # The list of papers and their relevance scores

    questions: list[tuple[SurveyQuestion, float | None]] # The list of questions and their relevance scores

    __trace_file__ : Optional[str] = None # The file to which the status is saved. If None, it is not saved to a file.
    # Any time the status is updated, a new line with the updated status is written to the file.
    # In Python, holding a file handle is not recommended, so we will open and close the file each time we write to it.

    def __init__(self, trace_file: str | None = None):
        """Initializes the RequestStatus object.
        If trace_file is given, the status will be saved to that file.
        """
        self.papers = []
        self.questions = []
        self.__trace_file__ = trace_file

    def pretty_print(self):
        """Prints the status of the request in a human-readable format."""
        print(f"Request status: {self.__dict__}") # TODO: Add a better pretty print function

    # By overriding the __setattr__ method, we can make sure that the status is always printed when it is updated.
    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        # Pretty print the status when it is updated.
        if name == "papers" or name == "questions":
            self.pretty_print()

        # If a trace file is set, write the status to the file.
        if self.__trace_file__ is not None:
            with open(self.__trace_file__, "a") as f:
                # Serialize the entire status to a string and write it to the file.
                self_serialized = str(self.__dict__)
                f.write(self_serialized + "\n") # Write the status to the file, one line per update.


    # Besides the setattr, we can also override the __getattr__ method for the few times where the papers or questions are modified.
    def __getattr__(self, name):
        # First make sure that it's only done for the papers and questions.
        if name == "papers" or name == "questions":
            self.pretty_print()
        return super().__dict__[name] # Is this correct?