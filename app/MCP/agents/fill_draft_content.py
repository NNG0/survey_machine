from .base import run_basic_ollama_agent
from ..types import RequestStatus, StepInformation


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
        key_qs = [q[0] for q in (status.key_questions or [])]
    except Exception:
        key_qs = []
    key_qs_str = "\n".join([f"- {q}" for q in key_qs]) if key_qs else "(none)"

    prior_sections_md = "\n\n".join(
        [f"{h.title}" for h in status.draft[:next_idx] if h.content]
        # [f"{h.title}\n\n{h.content}" for h in status.draft[:next_idx] if h.content]
    )  # TODO: Is this a good idea? This is probably too much context for the LLM.
    # I'll disable it for now, but that also means that the content might be repeated.
    # Depending on the LLM, we might want to enable this after some testing.

    prompt = f"""
    You are drafting a literature review section. Write the full markdown content for the given heading.

    Research question:
    {status.settings.research_question}

    Key questions:
    {key_qs_str}

    Heading to write:
    {heading.title}

    Previously written sections (for context, do not repeat headings):
    {prior_sections_md if prior_sections_md else "(none)"}

    Requirements:
    - Output markdown content only, no JSON, no backticks.
    - Be concise but substantive (150-300 words for top-level, 80-200 for subsections).
    - Use markdown urls for citation: [Author, Year](http://example.com) if needed; do not fabricate URLs.
    - Keep tone academic and neutral.
    """

    response = await run_basic_ollama_agent(
        name="fill_draft_content",
        prompt=prompt,
        server_list=[],
        output_type=str,
    )

    if isinstance(response, Exception):
        step_info.add_error(
            f"Error filling content for heading '{heading.title}': {response}"
        )
        return status, step_info

    if not isinstance(response, str) or not response.strip():
        step_info.add_warning("Agent did not return content text.")
        return status, step_info

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
