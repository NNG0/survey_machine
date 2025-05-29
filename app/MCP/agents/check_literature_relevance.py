from typing import Optional
from .base import run_basic_ollama_agent
from MCP.types import Article


async def run_check_literature_relevance_agent(article: Article, research_question: str) -> Optional[float]:
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
        output_type=float
    )