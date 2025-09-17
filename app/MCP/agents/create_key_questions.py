from .base import run_basic_ollama_agent
from ..types import RequestStatus, StepInformation


async def run_single_create_key_questions_agent(
    status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Dummy function to keep the interface consistent. Does the same thing as run_all_create_key_questions_agent."""
    status, step_info = await run_all_create_key_questions_agent(status)
    step_info.add_warning("Please use the run_all_create_key_questions_agent instead.")
    return status, step_info


async def run_all_create_key_questions_agent(
    status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the single create key questions agent."""
    step_info = StepInformation()

    prompt = f"""
    You are a research assistant helping to create key questions for a literature review.
    Your task is to generate {status.settings.num_key_questions} key questions based on the following research question:
    {status.settings.research_question}
    """
    key_questions = await run_basic_ollama_agent(
        name="create_key_questions",
        prompt=prompt,
        server_list=[],
        output_type=list[str],
    )
    # if key_questions == (True,):
    #     step_info.add_error("Rate limit exceeded while creating key questions.")
    # elif key_questions == (False,):
    #     step_info.add_error("Failed to create key questions due to an unknown error.")
    if isinstance(key_questions, tuple):
        if key_questions[0]:
            step_info.add_error("Rate limit exceeded while creating key questions.")
        else:
            step_info.add_error(
                "Failed to create key questions due to an unknown error."
            )
    elif isinstance(key_questions, Exception):
        step_info.add_error(f"Error creating key questions: {key_questions}")
    elif key_questions:
        status.key_questions = [
            (k, None, None) for k in key_questions
        ]  # Assign None as the source paper
    else:
        print(
            "Error: The create key questions agent did not return a list of questions."
        )
        print(key_questions)
        step_info.add_error("Error creating key questions.")
    return status, step_info
