from typing import List, Optional
from .base import run_basic_ollama_agent
from MCP.types import Article, RequestStatus, StepInformation


async def run_check_literature_relevance_agent(
    article: Article, research_question: str
) -> Optional[float]:
    """This agent receives an article and a research question and returns an estimated relevance score for the article between 0 and 1.
    The higher the score, the more relevant the article is to the research question.
    """

    prompt = f"""
You are a professional research assistant. Given a research question and an article, you need to estimate the relevance of the article to the research question.
Only based on the title, abstract and author of the article, return a score between 0 and 1 for the relevance of the article to the research question.

research question: {research_question}

Article: {article.title} by {article.author}
Abstract: {article.abstract}
"""
    return await run_basic_ollama_agent(
        name="relevant_literature_agent",
        prompt=prompt,
        server_list=[],
        output_type=float,
    )


async def run_single_check_literature_relevance_agent(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the check_literature_relevance agent on the next article in the request status,
    assigning a relevance score to it if it is not already set.
    """

    step_info = StepInformation()

    # Because we can't modify the request status in place, we need to modify it outside of the loop.
    to_change: Optional[tuple[int, float]] = None

    for i, (article, relevance) in enumerate(request_status.papers):
        # Only if the relevance is None, we need to check it.
        if relevance is None:
            # Run the agent on the article.
            relevance = await run_check_literature_relevance_agent(
                article, request_status.settings.research_question
            )
            if relevance is not None and isinstance(relevance, float):
                to_change = (i, relevance)
                break  # We found an article to change, so we can break the loop.
            elif isinstance(relevance, Exception):
                step_info.add_error(
                    f"Error checking relevance of paper {article.title}: {relevance}"
                )
                continue
            else:
                step_info.add_error(
                    f"Error checking relevance of paper {article.title}, skipping."
                )

        # If the relevance is already set, we can skip it.
    if to_change is not None:
        # Update the request status with the new relevance score.
        request_status.papers[to_change[0]] = (
            request_status.papers[to_change[0]][0],
            to_change[1],
        )

    return (request_status, step_info)  # Return the updated request status.


async def run_all_check_literature_relevance_agent(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the check_literature_relevance agent on all articles in the request status."""

    step_info = StepInformation()
    to_change: List[tuple[int, float]] = []

    for i, (article, relevance) in enumerate(request_status.papers):
        # Only if the relevance is None, we need to check it.
        if relevance is None:
            # Run the agent on the article.
            relevance = await run_check_literature_relevance_agent(
                article, request_status.settings.research_question
            )
            if relevance is not None and isinstance(relevance, float):
                to_change.append((i, relevance))
            elif isinstance(relevance, Exception):
                step_info.add_error(
                    f"Error checking relevance of paper {article.title}: {relevance}"
                )
                continue
            else:
                step_info.add_error(
                    f"Error checking relevance of paper {article.title}, skipping."
                )

    # Update the request status with the new relevance scores.
    for i, relevance in to_change:
        request_status.papers[i] = (request_status.papers[i][0], relevance)
    else:
        step_info.add_warning("No more papers to check relevance for.")

    return (
        request_status,
        step_info,
    )  # Return the updated request status and step info.
