from .base import run_basic_ollama_agent
from ..types import DraftHeading, RequestStatus, StepInformation


async def run_single_create_draft_headings_agent(
    status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Dummy function to keep the interface consistent. Does the same as run_all_create_draft_headings_agent."""
    status, step_info = await run_all_create_draft_headings_agent(status)
    step_info.add_warning("Please use the run_all_create_draft_headings_agent instead.")
    return status, step_info


async def run_all_create_draft_headings_agent(
    status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Create initial draft headings for the final document based on the research question and key questions."""
    step_info = StepInformation()

    # If draft already exists, don't run the agent again.
    if status.draft and len(status.draft) > 0:
        step_info.add_warning("Draft headings already exist, skipping creation.")
        return status, step_info

    # This agent effectively needs access to the entire state to run well, so we format the status in a nice way for it.

    key_questions = []
    if status.key_questions and isinstance(status.key_questions, list):
        for q in status.key_questions:
            if isinstance(q, tuple) and len(q) >= 1 and isinstance(q[0], str):
                key_questions.append(q[0])

    key_qs_str = (
        "\n".join([f"- {q}" for q in key_questions]) if key_questions else "(none yet)"
    )

    prompt = f"""
    You are a research assistant helping to draft a structured literature review.
    Create a clean, logically ordered list of markdown headings for the review outline.
    Use the research question and, if available, the key questions to decide the outline.

    Research question:
    {status.settings.research_question}

    Key questions:
    {key_qs_str}

    Requirements:
    - Return a list of strings, each a markdown heading.
    - The title must include the markdown hashes for the level (e.g., "# Introduction", "## Methods").
    - Do not include any content, only the headings.
    - Include standard sections like Introduction, Background/Related Work, Methods, Results/Discussion (as appropriate), Limitations, and Conclusion; adapt names to fit the question.
    - Keep it concise: 6–10 headings total with reasonable nesting (use #, ##, and optionally ###).
    """

    # TODO: rework the sections the agent is told to use
    # Also maybe give the agent the ability to read the relevant papers? That would be quite hard to do right though.

    response = await run_basic_ollama_agent(
        name="create_draft_headings",
        prompt=prompt,
        server_list=[],
        output_type=list[str],
    )

    if response == (True,):
        step_info.add_error("Rate limit exceeded while creating draft headings.")
        return status, step_info
    elif response == (False,):
        step_info.add_error("Failed to create draft headings due to an unknown error.")
        return status, step_info
    elif isinstance(response, Exception):
        step_info.add_error(f"Error creating draft headings: {response}")
        return status, step_info

    if (
        response is None
        or not isinstance(response, list)
        or not all(isinstance(h, str) for h in response)
    ):
        step_info.add_error("Agent did not return a valid list of str.")
        return status, step_info

    headings_from_response = [DraftHeading(title=h, content=None) for h in response]

    if not headings_from_response:
        step_info.add_error("No valid headings produced.")
        return status, step_info

    status.draft = headings_from_response

    return status, step_info
