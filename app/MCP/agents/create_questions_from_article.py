from typing import Optional
from .base import run_basic_ollama_agent
from MCP.types import Article

async def run_create_questions_from_article_agent(article: Article, research_question: str) -> Optional[list[str]]:
    """This agent receives an article and a research question and returns a list of questions to ask the surveytakers. 
    They are supposed to be open-ended and not correctly formatted yet. 
    """

    prompt = f"""Create survey questions about this research topic.

                RESEARCH TOPIC: {research_question}

                ARTICLE INFO:
                Title: {article.title}
                Author: {article.author}  
                Abstract: {article.abstract}

                Create exactly 3 survey questions. Output format:
                ["Question 1", "Question 2", "Question 3"]

                Questions:"""
    # TODO: Here, both few-shot and RAG should be used.
    return await run_basic_ollama_agent(
        name="create_questions_from_article_agent",
        prompt=prompt,
        server_list=[],
        output_type=list[str]
    )
