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

    if (
        status.key_questions
        and len(status.key_questions) >= status.settings.num_key_questions
    ):
        step_info.add_warning(
            "Requested amount of key questions already created, skipping step."
        )
        return status, step_info  # Key questions already created.

    prompt = f"""
    You are a research assistant.  

    Generate exactly {status.settings.num_key_questions} key questions for this research question:

    "{status.settings.research_question}"

    Return ONLY a valid JSON array of strings.  
    Example output:
    ["What is ...?", "How does ...?", "In which cases ...?"]

    Do not include explanations or additional text.
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
    elif key_questions:
        new_key_questions = [
            (k, None, None) for k in key_questions
        ]  # Assign None as the source paper
        if status.key_questions is None:
            status.key_questions = []
        status.key_questions.extend(new_key_questions)
    else:
        print(
            "Error: The create key questions agent did not return a list of questions."
        )
        print(key_questions)
        step_info.add_error("Error creating key questions.")
    return status, step_info
