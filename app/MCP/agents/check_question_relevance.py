from typing import Optional
from .base import run_basic_ollama_agent

async def run_check_question_relevance_agent(question: str, research_question: str) -> Optional[float]:
    """This agent receives a question and a research question and returns an estimated relevance score for the question between 0 and 1.
    The higher the score, the more relevant the question is to the research question.
    """

    prompt = f"""
You are a professional research assistant. Given a research question and another question, which will be asked in a survey, you need to estimate the relevance of the question to the research question.
Only based on the content of the question, return a score between 0 and 1 for the relevance of the question to the research question.
Research question: {research_question}
Question: {question}""" 
    return await run_basic_ollama_agent(
        name="check_question_relevance_agent",
        prompt=prompt,
        server_list=[],
        output_type=float
    )