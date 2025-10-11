from typing import Tuple
from .base import run_basic_ollama_agent
from ..types import RequestStatus, StepInformation


# The function that adjusts the question asks the model to assign the question to a specific paper
# and maybe adjust the question a bit.
async def run_single_adjust_questions_agent(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Assigns the next unassigned key question one or more papers, by their URLs."""

    # TODO: Allow the agent to also adjust the question text if needed.

    step_info = StepInformation()

    # It can't run if there are no key questions.
    if not request_status.key_questions:
        step_info.add_error(
            "No key questions to adjust or assign papers to. Please generate or write them first."
        )
        return request_status, step_info

    question_and_index = next(
        (
            (q, i)
            for i, q in enumerate(request_status.key_questions)
            if q[1] is None or len(q[1]) == 0
        ),
        None,
    )

    if question_and_index is None:
        step_info.add_warning("All key questions have been assigned to papers.")
        return request_status, step_info

    question, question_index = question_and_index

    # We can now ask the model to adjust the question and assign it to a paper.
    # It needs to get the papers to assign the question the url.

    prompt = f"""
    You are a research assistant. Given a key question for a survey paper, return the list of URLs of the papers that are relevant to the question.
    Output only the URLs.

    Key question: {question[0]}
    Papers (with their problem questions and URLs):
    {"\n".join(f"{paper.article.title}: {paper.problem_questions} ({paper.article.url})" for paper in request_status.papers)}
    Output only the URLs:
    """
    # TODO: Maybe give the agent the ability to slightly adjust the question?
    response = await run_basic_ollama_agent(
        name="adjust_questions",
        prompt=prompt,
        output_type=list[str],
        server_list=["literature_access", "fetch"],
    )

    if response is not None and isinstance(response, list) and len(response) > 0:
        question = (question[0], response, question[2])
        request_status.key_questions[question_index] = question
    elif isinstance(response, Exception):
        step_info.add_error(
            f"Failed to adjust question at index {question_index}: {response}"
        )
    elif isinstance(response, Tuple):
        if response[0]:
            step_info.add_error("Rate limit exceeded while adjusting question.")
        else:
            step_info.add_error("Failed to adjust question due to an unknown error.")
    else:
        step_info.add_warning("Failed to add URL to question.")
        print(f"Wrong Response type: {response}")

    return request_status, step_info


async def run_all_adjust_questions_agent(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Assigns all unassigned key questions to specific papers, by their URLs."""

    step_info = StepInformation()

    if not request_status.key_questions:
        step_info.add_error(
            "No key questions to adjust or assign papers to. Please generate or write them first."
        )
        return request_status, step_info

    # The function to run a single one already exists.

    tried_at_this_index = 0
    last_tried_index = -1

    index = 0

    key_questions = request_status.key_questions

    while index < len(key_questions):
        if tried_at_this_index >= 3:
            step_info.add_warning(
                f"Failed to adjust question at index {index} after 3 attempts."
            )
            index += 1
            continue

        question = key_questions[index]
        if index == last_tried_index:
            tried_at_this_index += 1
        else:
            tried_at_this_index = 1
        last_tried_index = index

        if question[1] is None:
            # If the question has not been assigned yet, run the adjusting agent.
            agent_result = await run_single_adjust_questions_agent(request_status)
            # status, info = await run_single_adjust_questions_agent(request_status)
            # step_info.merge(info)
            # if status is not None:
            #     request_status = status
            #     if request_status.key_questions is not None:
            #         key_questions = request_status.key_questions
            if isinstance(agent_result, Exception):
                step_info.add_error(
                    f"Failed to adjust question at index {index}: {agent_result}, trying again."
                )
                continue
            status, info = agent_result
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
