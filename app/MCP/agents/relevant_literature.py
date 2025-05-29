from typing import Optional
from .base import run_basic_ollama_agent
from MCP.types import Article

async def run_relevant_literature_agent(research_question: str, paper_limit: int) -> Optional[list[Article]]:
    """This agent receives the research question and returns a list of relevant literature in the proper format."""

    prompt = f"""
    You are a research assistant. Given a research question, you need to find relevant literature.
    You have access to Google Scholar to look up papers. For the research question, find the most relevant papers and return a list of articles with their title, abstract, author and URL.
    Limit the number of articles to {paper_limit}.
    research question: {research_question}""" # TODO: Add examples on how to do this, multi-shot learning is important

    return await run_basic_ollama_agent(
        name="relevant_literature_agent",
        prompt=prompt,
        server_list=["google_scholar"],
        output_type=list[Article]
    )



# TODO: Put test here