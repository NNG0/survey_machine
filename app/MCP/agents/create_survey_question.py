from typing import Optional
from .base import run_basic_ollama_agent
from MCP.types import SurveyQuestion

async def run_create_survey_question_agent(question: str, research_question: str) -> Optional[SurveyQuestion]:
    """This agent receives a question and the main research question and returns a correctly formatted survey question."""

    prompt = f"""
You are a professional research assistant. You will be creating a survey for a research question.
Given a question, you need to think ybout how it will be answered and output correctly formatted survey question.

Research question: {research_question}
Question: {question}"""

    return await run_basic_ollama_agent(
        name="create_survey_question_agent",
        prompt=prompt,
        server_list=[],
        output_type=SurveyQuestion
    )
