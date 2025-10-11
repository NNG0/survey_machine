from .base import run_basic_ollama_agent
from ..types import RequestStatus, StepInformation, SurveyResult


# The function takes the next key question that does not have a result yet
# and extracts the result from the papers.
async def run_single_extract_results_agent(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Extracts results from the papers for the next key question."""
    step_info = StepInformation()

    if not request_status.key_questions or len(request_status.key_questions) == 0:
        step_info.add_error("No key questions to extract results from.")
        return request_status, step_info

    # Find the next key question that does not have a result yet.
    question_and_index = next(
        ((q, i) for i, q in enumerate(request_status.key_questions) if q[2] is None),
        None,
    )

    if question_and_index is None:
        step_info.add_warning("All key questions have results.")
        return request_status, step_info

    question, question_index = question_and_index

    # We can now ask the model to extract the result from the papers.
    prompt = f"""
    You are a research assistant. Given a key question for a survey paper, Write a summary of the findings from the papers as the result.
    It should be informative, but concise. Use a maximum of 300 words.
    Key question: {question[0]}
    Papers: {request_status.papers}
    """

    response = await run_basic_ollama_agent(
        name="extract_results",
        prompt=prompt,
        output_type=SurveyResult,
        server_list=["literature_access", "fetch"],
    )

    if response == (True,):
        step_info.add_error("Rate limit exceeded while extracting results.")
    elif response == (False,):
        step_info.add_error(
            f"Failed to extract result for question at index {question_index} due to an unknown error."
        )
    elif response is not None and isinstance(response, SurveyResult):
        question = (question[0], question[1], response)
        request_status.key_questions[question_index] = question
    elif isinstance(response, Exception):
        step_info.add_error(
            f"Failed to extract result for question at index {question_index}: {response}"
        )
    else:
        step_info.add_warning("Failed to extract result.")

    return request_status, step_info


# The same but with all key questions
async def run_all_extract_results_agent(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Extracts results from the papers for all key questions."""
    step_info = StepInformation()

    if not request_status.key_questions:
        step_info.add_error("No key questions to extract results from.")
        return request_status, step_info

    # We reuse the function that runs on a single question.
    # This isn't encoded, but both functions must agree that at least
    # one question is unprocessed for the single extract call to work.

    tried_at_this_index = 0
    last_tried_index = -1

    index = 0

    key_questions = request_status.key_questions

    while index < len(key_questions):
        if tried_at_this_index >= 3:
            step_info.add_warning(
                f"Failed to extract results for question: {key_questions[index][0]} at index {index} after 3 tries."
            )
            index += 1
            continue

        question = key_questions[index]
        if index == last_tried_index:
            tried_at_this_index += 1
        else:
            tried_at_this_index = 1
        last_tried_index = index

        if question[2] is None:
            # If the question does not yet have a result, run the single agent.
            result = await run_single_extract_results_agent(request_status)
            # status, info = result
            # step_info.merge(info)
            # if status is not None:
            #     request_status = status
            #     if request_status.key_questions is not None:
            #         key_questions = request_status.key_questions
            if isinstance(result, Exception):
                step_info.add_error(
                    f"Failed to extract results for question: {question[0]} at index {index}: {result}, trying again."
                )
                continue
            status, info = result
            step_info.merge(info)
            if status is not None:
                request_status = status
                if (
                    request_status.key_questions is not None
                    and len(request_status.key_questions) > index
                ):
                    key_questions[index] = request_status.key_questions[index]

    request_status.key_questions = key_questions
    return request_status, step_info
