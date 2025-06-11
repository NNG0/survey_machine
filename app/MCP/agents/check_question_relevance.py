from typing import Optional

from MCP.types import RequestStatus, StepInformation
from .base import run_basic_ollama_agent


async def run_check_question_relevance_agent(
    question: str, research_question: str
) -> Optional[float]:
    """This agent receives a question and a research question and returns an estimated relevance score for the question between 0 and 1.
    The higher the score, the more relevant the question is to the research question.
    """

    prompt = f"""
You are a professional research assistant. Given a research question and another question, which will be asked in a survey, you need to estimate the relevance of the question to the research question.
Only based on the content of the question, return a score between 0 and 1 for the relevance of the question to the research question.
Research question: {research_question}
Question: {question}"""
    return await run_basic_ollama_agent(
        name="check_question_relevance_agent",
        prompt=prompt,
        server_list=[],
        output_type=float,
    )


async def run_single_check_question_relevance_agent(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the check_question_relevance agent on the next question in the request status,
    assigning a relevance score to it if it is not already set.
    """

    step_info = StepInformation()

    # Because we can't modify the request status in place, we need to modify it outside of the loop.
    to_change: Optional[tuple[int, float]] = None

    for i, (question, relevance) in enumerate(request_status.questions):
        # Only if the relevance is None, we need to check it.
        if relevance is None:
            # Run the agent on the question.
            relevance = await run_check_question_relevance_agent(
                question.question, request_status.settings.research_question
            )
            if relevance is not None:
                to_change = (i, relevance)
                break  # We found a question to change, so we can break the loop.
            else:
                step_info.add_error(
                    f"Error checking relevance of question {question.question}, skipping."
                )

    # If we found a question to change, we update the request status.
    if to_change is not None:
        i, relevance = to_change
        request_status.questions[i] = (request_status.questions[i][0], relevance)
    else:
        step_info.add_warning("No more questions to check relevance for.")

    return (request_status, step_info)


async def run_all_check_question_relevance_agent(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the check_question_relevance agent on all questions in the request status,
    assigning a relevance score to each question if it is not already set.
    """

    step_info = StepInformation()

    to_change: Optional[tuple[int, float]] = None

    for i, (question, relevance) in enumerate(request_status.questions):
        if relevance is None:
            # Run the agent on the question.
            relevance = await run_check_question_relevance_agent(
                question.question, request_status.settings.research_question
            )
            if relevance is not None:
                to_change = (i, relevance)
            else:
                step_info.add_error(
                    f"Error checking relevance of question {question.question}, skipping."
                )
    # If we found questions to change, we update the request status.
    if to_change is not None:
        i, relevance = to_change
        request_status.questions[i] = (request_status.questions[i][0], relevance)
    else:
        step_info.add_warning("No more questions to check relevance for.")
    return (request_status, step_info)
