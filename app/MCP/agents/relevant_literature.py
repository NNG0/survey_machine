from typing import Optional
from .base import run_basic_ollama_agent
from MCP.types import Article, RequestStatus, StepInformation, OpenRouter


async def run_relevant_literature_agent(
    research_question: str, paper_limit: int
) -> Optional[list[Article]]:
    """This agent receives the research question and returns a list of relevant literature in the proper format."""

    # DEBUG
    print(f"Running relevant literature agent for question: {research_question}")

    prompt = f"""
    You are a research assistant. Given a research question, you need to find relevant literature.
    You have access to Google Scholar to look up papers. For the research question, find the most relevant papers and return a list of articles with their title, abstract, author and URL.
    Limit the number of articles to {paper_limit}.
    research question: {research_question}"""  # TODO: Add examples on how to do this, multi-shot learning is important

    return await run_basic_ollama_agent(
        name="relevant_literature_agent",
        prompt=prompt,
        server_list=["google_scholar"],
        output_type=list[Article],
        custom_provider=OpenRouter(),  # Use the OpenRouter for better performance, at the cost of one of the 50 tokens we get daily.
    )


async def run_single_relevant_literature_agent(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the relevant_literature agent on the request status to find relevant literature for the research question."""

    step_info = StepInformation()

    # If we already have papers, we don't need to run the agent again.
    if request_status.papers:
        step_info.add_warning(
            "Papers already found, skipping relevant literature agent."
        )
        return request_status, step_info

    # Run the agent to find relevant literature.
    articles = await run_relevant_literature_agent(
        request_status.settings.research_question, request_status.settings.paper_limit
    )

    if articles is not None and isinstance(articles, list):
        request_status.papers = [(article, None) for article in articles]
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


# TODO: Put test here
