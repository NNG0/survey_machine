from typing import List, Optional
from .base import run_basic_ollama_agent
from MCP.types import RequestStatus, StepInformation, SurveyQuestion


async def run_create_survey_question_agent(
    question: str, research_question: str
) -> Optional[SurveyQuestion]:
    """This agent receives a question and the main research question and returns a correctly formatted survey question."""

    prompt = f"""
You are a professional research assistant. You will be creating a survey for a research question.
Given a question, you need to think ybout how it will be answered and output correctly formatted survey question.
The question should either be a text field, multiple choice, yes/no or a range question.
The options should be set accordingly. 
For example, if the question has a range answer, the options should be a tuple of two integers representing the minimum and maximum values.
And if the question is a multiple choice question, the options should be a list of strings representing the possible answers.

Research question: {research_question}
Question: {question}"""

    return await run_basic_ollama_agent(
        name="create_survey_question_agent",
        prompt=prompt,
        server_list=[],
        output_type=SurveyQuestion,
    )


async def run_single_create_survey_question_agent(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the create_survey_question agent on the next question in the request status,
    adding the answer type and options to the question."""

    step_info = StepInformation()

    # Because we can't modify the request status in place, we need to modify it outside of the loop.
    to_change: Optional[tuple[int, SurveyQuestion]] = None

    for i, (question, relevance) in enumerate(request_status.questions):
        # Only if the question is not already formatted, we need to check it.
        if question.answer_type is None or question.options is None:
            # Run the agent on the question.
            formatted_question = await run_create_survey_question_agent(
                question.question, request_status.settings.research_question
            )

            # Asyncio library exception handling
            if formatted_question is not None and isinstance(
                formatted_question, SurveyQuestion
            ):
                to_change = (i, formatted_question)
                break  # We found a question to change, so we can break the loop.
            elif isinstance(formatted_question, Exception):
                step_info.add_error(
                    f"Error formatting question {question.question}: {formatted_question}"
                )
                continue  # Skip to the next question if there was an error.
            else:
                step_info.add_error(
                    f"Error formatting question {question.question}, skipping."
                )

    # If we found a question to change, we update the request status.
    if to_change is not None:
        i, formatted_question = to_change
        request_status.questions[i] = (
            formatted_question,
            request_status.questions[i][
                1
            ],  # Keep the relevance score unchanged. This should never be relevant, but if something weird happened, not having this might cause issues.
        )
    else:
        step_info.add_warning("No more questions to format.")

    return request_status, step_info


async def run_all_create_survey_questions_agent(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the create_survey_question agent on all questions in the request status,
    adding the answer type and options to each question."""

    step_info = StepInformation()

    # If there are no questions, we can't create survey questions.
    if len(request_status.questions) == 0:
        step_info.add_error("No questions to process.")
        return request_status, step_info

    to_change: List[tuple[int, SurveyQuestion]] = []

    # Process each question in the request status.
    for i, (question, relevance) in enumerate(request_status.questions):
        formatted_question = await run_create_survey_question_agent(
            question.question, request_status.settings.research_question
        )
        if formatted_question is None:
            step_info.add_error(
                f"Error formatting question {question.question}, skipping."
            )
            continue

        # Asyncio library exception handling
        if isinstance(formatted_question, Exception):
            step_info.add_error(
                f"Error formatting question {question.question}: {formatted_question}"
            )
            continue

        # Add the formatted question to the list of questions to change.
        to_change.append((i, formatted_question))

    # Update the request status with the new formatted questions.
    for i, formatted_question in to_change:
        request_status.questions[i] = (
            formatted_question,
            request_status.questions[i][1],  # Keep the relevance score unchanged.
        )
    else:
        step_info.add_warning("No more questions to format.")
    return request_status, step_info  # Return the updated request status and step info.
