from typing import Optional
from .base import run_basic_ollama_agent
from MCP.types import Article, RequestStatus, StepInformation

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from literature_db_access.open_alex_client import run_enhanced_openalex_search



async def generate_similar_research_questions(original_question: str, num_variations: int = 4) -> list[str]:
    """Generate similar research questions + keep the original"""
    
    prompt = f"""
    SYSTEM:
    You are a research assistant. Paraphrase research questions.

    USER:
    Paraphrase the following research question into exactly {num_variations} different variations.
    Guidelines:
    - Keep the core meaning and research focus
    - 10–20 words each
    - Use synonyms and different sentence structures
    - English language
    - Return only a JSON array, no markdown, no commentary

    Original:
    ```{original_question}```

    Few-shot example:
    Original: "How does remote work affect productivity?"
    Answer: ["What is the impact of telecommuting on employee performance?",
            "Does working from home influence organizational efficiency?",
            "Remote work effects on workplace productivity metrics",
            "Telework and its relationship to professional output"]
    """
    
    try:
        variations = await run_basic_ollama_agent(
            name="question_generator",
            prompt=prompt,
            server_list=[],
            output_type=list[str]
        )
        
        if variations and len(variations) >= num_variations:
            all_questions = [original_question] + variations[:num_variations]
            
            # Display generated questions
            print(f"\n Generated {len(all_questions)} research question variations:")
            for i, question in enumerate(all_questions, 1):
                print(f"  {i}. {question}")
            print()
            
            return all_questions
        else:
            return [original_question]
            
    except Exception as e:
        print(f"Error generating questions: {e}")
        return [original_question]


async def run_relevant_literature_agent(research_question: str, paper_limit: int) -> Optional[list[Article]]:
    """Literature search using direct OpenAlex API instead of Google Scholar MCP"""
    
    print(f"Using OpenAlex API for literature search: {research_question}")
    
    # Generate query variations
    variations = await generate_similar_research_questions(research_question)
    
    # Prepare all queries (original + variations) 
    all_queries = variations  # generate_similar_research_questions returns original + variations
    
    try:
        articles = await run_enhanced_openalex_search(
            research_question=research_question,
            paper_limit=paper_limit,
            email=None
        )
        
        print(f"OpenAlex search complete: {len(articles) if articles else 0} articles found")
        return articles if articles else None
        
    except Exception as e:
        print(f"Error with OpenAlex client: {e}")
        return None


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