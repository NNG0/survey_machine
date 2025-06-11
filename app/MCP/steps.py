# File that determines what steps to do next in the agent workflow.

# It depends on all the agents, so you should pretty much only import it in the main file
from typing import Awaitable, Callable
from MCP.types import RequestStages, RequestStatus, StepInformation
from MCP.agents.check_literature_relevance import (
    run_single_check_literature_relevance_agent,
    run_all_check_literature_relevance_agent,
)
from MCP.agents.check_question_relevance import (
    run_all_check_question_relevance_agent,
    run_single_check_question_relevance_agent,
)
from MCP.agents.create_survey_question import (
    run_single_create_survey_question_agent,
    run_all_create_survey_questions_agent,
)
from MCP.agents.relevant_literature import (
    run_all_relevant_literature_agent,
    run_single_relevant_literature_agent,
)
from MCP.agents.create_questions_from_article import (
    run_all_create_questions_from_article_agent,
    run_single_create_questions_from_article_agent,
)


def next_step(
    status: RequestStatus,
) -> (
    tuple[
        str,
        Callable[[RequestStatus], Awaitable[tuple[RequestStatus, StepInformation]]],
        Callable[[RequestStatus], Awaitable[tuple[RequestStatus, StepInformation]]],
        RequestStages,
    ]
    | None
):
    """Recieves the current status of the request and returns the next step to take.
    Returns None if the request is finished.
    The first object in the return tuple is a human-readable string describing the step.
    The second object is the function to call to execute the step.
    The third object is the function to call to execute the step until another operation is needed.
    The fourth object is the Enum that describes the step.
    """

    # The very first step is to run the relevant literature agent.
    # This is dependent on whether there are already papers in the request status.
    if not status.papers:
        return (
            "Finding relevant literature",
            run_single_relevant_literature_agent,
            run_all_relevant_literature_agent,
            RequestStages.FINDING_LITERATURE,
        )

    # Next, we check if there are any papers that need to be checked for relevance.
    if any(relevance is None for _, relevance in status.papers):
        return (
            "Checking relevance of literature",
            run_single_check_literature_relevance_agent,
            run_all_check_literature_relevance_agent,
            RequestStages.CHECKING_LITERATURE_RELEVANCE,
        )

    # If we have papers, we can move on to the next step.
    # If there are no questions or not enough questions, we need to create them.
    # TODO: If ever a question reworker agent is implemented, we need to make sure we don't revert back to this step.
    if (
        not status.questions
        or len(status.questions)
        < status.settings.paper_limit * status.settings.question_per_article
    ):
        return (
            "Creating survey questions",
            run_single_create_questions_from_article_agent,
            run_all_create_questions_from_article_agent,
            RequestStages.CREATING_SURVEY_QUESTIONS,
        )

    # If we have questions, but some of them need to be checked for relevance, we need to do that.
    if any(relevance is None for _, relevance in status.questions):
        return (
            "Checking relevance of survey questions",
            run_single_check_question_relevance_agent,
            run_all_check_question_relevance_agent,
            RequestStages.CHECKING_QUESTION_RELEVANCE,
        )

    # Lastly, we need to format all the questions to be survey questions.
    # This means that all questions should have an answer type and options.
    if any(
        question.answer_type is None or question.options is None
        for question, _ in status.questions
    ):
        return (
            "Formatting survey questions",
            run_single_create_survey_question_agent,
            run_all_create_survey_questions_agent,
            RequestStages.FORMATTING_SURVEY_QUESTIONS,
        )

    # If we reach this point, all steps are done.
    return None


# Some functions to make running the agents easier.
async def run_single_next_step(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the next step in the request status."""
    step_info = StepInformation()
    step = next_step(request_status)

    if step is None:
        step_info.add_warning("No more steps to take.")
        return request_status, step_info  # No more steps to take.

    name, single_step_fn, all_step_fn, _ = step
    request_status, step_info = await single_step_fn(request_status)

    return request_status, step_info


async def run_single_stage(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run all steps in the request status for this single stage."""
    step_info = StepInformation()
    step = next_step(request_status)

    if step is None:
        step_info.add_warning("No more steps to take.")
        return request_status, step_info  # No more steps to take.

    name, single_step_fn, all_step_fn, _ = step
    request_status, step_info = await all_step_fn(request_status)

    return request_status, step_info


async def run_until_before_stage(
    request_status: RequestStatus,
    stage: RequestStages,
) -> tuple[RequestStatus, StepInformation]:
    """Run all steps in the request status until the specified stage is reached."""
    step_info = StepInformation()

    while True:
        step = next_step(request_status)

        if step is None or step[3] == stage:
            break  # No more steps to take or we reached the specified stage.

        name, single_step_fn, all_step_fn, _ = step
        request_status, step_info2 = await all_step_fn(request_status)
        # Add the step info to the step information.
        step_info.merge(step_info2)

    return request_status, step_info
