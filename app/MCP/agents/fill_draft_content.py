from .base import run_basic_ollama_agent
from ..types import KeyQuestion, RequestStatus, StepInformation


async def run_single_fill_draft_content_agent(
    status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Fill the content for the next draft heading that has no content yet."""
    step_info = StepInformation()

    # Find next heading without content
    next_idx = None
    for i, h in enumerate(status.draft):
        if h.content is None:
            next_idx = i
            break

    if next_idx is None:
        step_info.add_warning("No draft headings without content to fill.")
        return status, step_info

    heading = status.draft[next_idx]

    # Collect context from status so the agent has enough information to generate useful headings
    # This is probably the single most user-focused place of the entire workflow; the headings names will most likely be
    # adjusted by the user manually.
    key_qs = []
    try:
        # In order for the draft content agent to work well, it will need a lot of context, so we'll give it the full
        # key questions, that is, both the question, the references and the results
        key_qs = [format_key_question(q) for q in (status.key_questions or [])]
    except Exception:
        key_qs = []
    key_qs_str = "\n\n".join([f"{q}" for q in key_qs]) if key_qs else "(none)"

    prior_sections_md = "\n\n".join(
        [f"{h.title}\n{h.content}" for h in status.draft[:next_idx] if h.content]
    )
    # I've added the content back in, it was repeating itself too much across sections.

    # Also add the name of the next heading to write
    next_heading_title = "(none)"
    if next_idx + 1 < len(status.draft):
        next_heading_title = status.draft[next_idx + 1].title

    prompt = f"""
    You are drafting a literature review section. Write the full markdown content for the given heading.

    Research question:
    {status.settings.research_question}

    Key questions:
    {key_qs_str}

    Previously written sections (for context, do not repeat headings):
    {prior_sections_md if prior_sections_md else "(none)"}

    Next heading to write (for context, do not write this one yet):
    {next_heading_title}
    
    Heading to write:
    {heading.title}

    Requirements:
    - Output markdown content only, no JSON, no backticks.
    - Be concise but substantive (450-800 words for top-level, 200-400 for subsections).
    - Use markdown urls for citation (Structure: [Author, Year](URL)) if needed. If the URL does not occur in the list of URLs from the papers, verify that it is actually correct.
    - Keep tone academic and neutral.
    - Only use the papers that are listed in the key questions references.
    """

    response = await run_basic_ollama_agent(
        name="fill_draft_content",
        prompt=prompt,
        server_list=["literature_access", "fetch"],
        output_type=str,
    )

    if response == (True,):
        step_info.add_error(
            f"Rate limit exceeded while filling content for heading '{heading.title}'."
        )
        return status, step_info
    elif response == (False,):
        step_info.add_error(
            f"Failed to fill content for heading '{heading.title}' due to an unknown error."
        )
        return status, step_info
    elif isinstance(response, Exception):
        step_info.add_error(
            f"Error filling content for heading '{heading.title}': {response}"
        )
        return status, step_info

    if not isinstance(response, str) or not response.strip():
        step_info.add_warning("Agent did not return content text.")
        return status, step_info

    # The content is valid, we may want to remove a double heading:
    # The agent often likes to repeat the heading (but not always, so we can't rely on it)
    # So if the response starts with the heading title, we remove it.
    if response.strip().startswith(heading.title):
        response = response.strip()[len(heading.title) :].strip()

    status.draft[next_idx].content = response.strip()
    return status, step_info


async def run_all_fill_draft_content_agent(
    status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Fill content for all draft headings, attempting each heading up to 2 times if empty output is returned."""
    step_info = StepInformation()

    index = 0
    tries_at_this_index = 0
    last_idx = -1
    while index < len(status.draft):
        if status.draft[index].content is not None:  # If content is already filled
            index += 1
            tries_at_this_index = 0
            continue

        if last_idx == index:
            tries_at_this_index += 1
        else:
            tries_at_this_index = 1
        last_idx = index

        if tries_at_this_index > 2:
            step_info.add_warning(
                f"Skipping heading at index {index} after multiple unsuccessful attempts."
            )
            index += 1
            tries_at_this_index = 0
            continue

        status_result, info = await run_single_fill_draft_content_agent(status)
        step_info.merge(info)

        # If the result is successful
        if status_result is not None:
            status = status_result
            if status_result.draft[index].content is not None:
                index += 1
                tries_at_this_index = 0

    return status, step_info


def format_key_question(q: KeyQuestion) -> str:
    # We give the agent the actual key question, the references and the results
    question, references, result = q
    references_str = "\n".join([f"- {ref}" for ref in (references or [])])
    return f"Question: {question}\nReferences:\n{references_str}\nResult: {result.result if result else 'None'}"
