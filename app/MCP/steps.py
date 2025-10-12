# File that determines what steps to do next in the agent workflow.

# It depends on all the agents, so you should pretty much only import it in the main file
from typing import Awaitable, Callable

from .agents.extract_results import (
    run_all_extract_results_agent,
    run_single_extract_results_agent,
)

from .agents.adjust_key_questions import (
    run_all_adjust_questions_agent,
    run_single_adjust_questions_agent,
)

from .agents.create_key_questions import (
    run_all_create_key_questions_agent,
    run_single_create_key_questions_agent,
)
from .agents.parse_papers import (
    run_all_parse_papers_agent,
    run_single_parse_papers_agent,
)
from .types import RequestStages, RequestStatus, StepInformation
from .agents.relevant_literature import (
    run_all_relevant_literature_agent,
    run_single_relevant_literature_agent,
)
from .agents.create_draft_headings import (
    run_all_create_draft_headings_agent,
    run_single_create_draft_headings_agent,
)
from .agents.fill_draft_content import (
    run_all_fill_draft_content_agent,
    run_single_fill_draft_content_agent,
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
    # This is dependent on whether there are already key questions first created from the research question.
    if (
        status.key_questions is None
        or len(status.key_questions) < status.settings.num_key_questions
    ):
        return (
            "Creating key questions",
            run_single_create_key_questions_agent,
            run_all_create_key_questions_agent,
            RequestStages.CREATING_KEY_QUESTIONS,
        )
    # Next, we need to find relevant literature.
    # This is dependent on whether there are already papers in the request status.
    if not status.papers or len(status.papers) < status.settings.paper_limit:
        return (
            "Finding relevant literature",
            run_single_relevant_literature_agent,
            run_all_relevant_literature_agent,
            RequestStages.FINDING_LITERATURE,
        )

    # Now we do have papers, but the information about their problem questions and methods is still missing.
    if any(
        article.problem_questions is None
        or article.methods is None
        or len(article.problem_questions) == 0
        or len(article.methods) == 0
        for article in status.papers
    ):
        return (
            "Parsing papers",
            run_single_parse_papers_agent,
            run_all_parse_papers_agent,
            RequestStages.PARSE_PAPERS,
        )

    # If we have papers, we can move on to the next step.
    # We adjust the key questions to fit the papers better.
    # To mark this, each outputted paper of this step is assigned the paper it matches closely.
    # (key questions must at least contain one paper, because else it would have hit the CREATING_KEY_QUESTIONS part)
    if any(
        question[1] is None or len(question[1]) == 0
        for question in status.key_questions
    ):
        return (
            "Assigning papers to questions",
            run_single_adjust_questions_agent,
            run_all_adjust_questions_agent,
            RequestStages.ADJUST_KEY_QUESTIONS,
        )

    # Now, we need to extract results from the papers.
    # This is stored alongside the key questions to give each a solution.
    if any(question[2] is None for question in status.key_questions):
        return (
            "Extracting results from papers",
            run_single_extract_results_agent,
            run_all_extract_results_agent,
            RequestStages.EXTRACT_RELEVANT_RESULTS_FROM_PAPERS,
        )

    # For the draft, first, the heading need to be created.
    if not status.draft or len(status.draft) == 0:
        return (
            "Creating draft headings",
            run_single_create_draft_headings_agent,
            run_all_create_draft_headings_agent,
            RequestStages.CREATING_DRAFT_HEADINGS,
        )

    # And the content of the headings needs to be filled, too.
    if any(heading.content is None for heading in status.draft):
        return (
            "Filling draft heading content",
            run_single_fill_draft_content_agent,
            run_all_fill_draft_content_agent,
            RequestStages.FILLING_DRAFT_CONTENT,
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

    _name, single_step_fn, _all_step_fn, _ = step
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

    # DEBUG
    # print(f"Running step: {step[0]}")

    _name, _single_step_fn, all_step_fn, _ = step
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

        _name, _single_step_fn, all_step_fn, _ = step
        request_status, step_info2 = await all_step_fn(request_status)
        # Add the step info to the step information.
        step_info.merge(step_info2)

    return request_status, step_info
