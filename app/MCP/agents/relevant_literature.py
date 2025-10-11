from typing import Optional, Tuple
from .base import run_basic_ollama_agent
from ..types import (
    Article,
    LLMArticle,
    RawArticle,
    RequestStatus,
    StepInformation,
    OpenRouter,
    convert_llm_article_to_raw_article,
)


async def run_relevant_literature_agent(
    research_question: str, paper_limit: int
) -> Tuple[Optional[list[RawArticle]], StepInformation]:
    """This agent receives the research question and returns a list of relevant literature in the proper format."""

    # DEBUG
    print(f"Running relevant literature agent for question: {research_question}")

    prompt = f"""
    You are a research assistant. Given a research question, you need to find relevant literature.
    You have access to OpenAlex to look up papers. For the research question, find the most relevant papers and return a list of articles with their title, abstract, author and URL.
    Limit the number of articles to {paper_limit}.
    research question: {research_question}"""  # TODO: Add examples on how to do this, multi-shot learning is important

    # Note: this currently doesn't prevent duplicates in the case that papers should be added multiple times.
    # This however is not the recommended way of using the agent, so it's not a big issue right now.
    response = await run_basic_ollama_agent(
        name="relevant_literature_agent",
        prompt=prompt,
        server_list=["literature_access", "fetch"],
        output_type=list[LLMArticle],
        custom_provider=OpenRouter(),  # Use the OpenRouter for better performance, at the cost of one of the 50 tokens we get daily.
    )

    step_info = StepInformation()

    if response is None:
        step_info.add_error("No response from relevant literature agent.")
    elif isinstance(response, Exception):
        step_info.add_error(f"Error from relevant literature agent: {response}")
    elif response == (True,):
        step_info.add_error("Rate limit exceeded while fetching relevant literature.")
    elif response == (False,):
        step_info.add_error(
            "Failed to fetch relevant literature due to an unknown error."
        )
    elif isinstance(response, list) and all(
        isinstance(article, LLMArticle) for article in response
    ):
        # Convert LLMArticle to RawArticle
        rawArticles = [
            convert_llm_article_to_raw_article(article) for article in response
        ]
        return rawArticles, step_info
    else:
        step_info.add_warning("Unexpected response from relevant literature agent.")

    return None, step_info


async def run_single_relevant_literature_agent(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the relevant_literature agent on the request status to find relevant literature for the research question."""

    step_info = StepInformation()

    articles_to_find = request_status.settings.paper_limit - len(request_status.papers)

    # If we already have enough papers, we don't need to run the agent again.
    if articles_to_find <= 0:
        step_info.add_warning(
            "Papers already found, skipping relevant literature agent."
        )
        return request_status, step_info

    # Run the agent to find relevant literature.
    articles, other_step_info = await run_relevant_literature_agent(
        request_status.settings.research_question, articles_to_find
    )
    step_info.merge(other_step_info)

    if (
        articles is not None
        and isinstance(articles, list)
        and len(articles) > 0
        and all(isinstance(article, RawArticle) for article in articles)
    ):
        new_papers = [
            Article(article=article, methods=None, problem_questions=None)
            for article in articles
        ]
        request_status.papers.extend(new_papers)
    elif isinstance(articles, Exception):
        step_info.add_error(f"Error finding relevant literature: {articles}")
    else:
        print("Error: The relevant literature agent did not return a list of articles.")
        print(articles)
        step_info.add_error("Error finding relevant literature.")

    return request_status, step_info


async def run_all_relevant_literature_agent(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Dummy function to keep the interface consistent. Does work, but should, if possible, be avoided in favor of the single agent."""

    request_status, step_info = await run_single_relevant_literature_agent(
        request_status
    )
    step_info.add_warning(
        "Please use run_single_relevant_literature_agent instead of run_all_relevant_literature_agent."
    )
    return request_status, step_info
