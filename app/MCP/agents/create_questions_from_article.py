from typing import Optional
from .base import run_basic_ollama_agent
from MCP.types import Article

async def run_create_questions_from_article_agent(article: Article, research_question: str) -> Optional[list[str]]:
    """This agent receives an article and a research question and returns a list of questions to ask the surveytakers. 
    They are supposed to be open-ended and not correctly formatted yet. 
    """

    prompt = f"""You are a professional research assistant. There will be a survey about the aricle you will recieve.
Based on the content of the article, create a list of questions that, when answered in the survey, will help answer the question.
Return the questions in a list format.
Research question: {research_question}.
Article: {article.title} by {article.author}
Abstract: {article.abstract}""" # TODO: Here, both few-shot and RAG should be used.
    return await run_basic_ollama_agent(
        name="create_questions_from_article_agent",
        prompt=prompt,
        server_list=[],
        output_type=list[str]
    )
