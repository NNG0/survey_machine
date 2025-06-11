from typing import Optional
from .base import run_basic_ollama_agent
from MCP.types import Article, RequestStatus, StepInformation, SurveyQuestion


async def run_create_questions_from_article_agent(
    article: Article, research_question: str, num_questions: int
) -> Optional[list[str]]:
    """This agent receives an article and a research question and returns a list of questions to ask the surveytakers.
    They are supposed to be open-ended and not correctly formatted yet.
    """

    # The prompt needs to be very specific about how many Questions there should be.
    question_output_hint = [f"Question {i + 1}" for i in range(num_questions)]
    question_output_hint = ", ".join(question_output_hint)
    question_output_hint = f'["{question_output_hint}"]'

    prompt = f"""Create survey questions about this research topic.

                RESEARCH TOPIC: {research_question}

                ARTICLE INFO:
                Title: {article.title}
                Author: {article.author}  
                Abstract: {article.abstract}

                Create exactly {num_questions} survey questions. Output format:
                {question_output_hint}

                Questions:"""
    # TODO: Here, both few-shot and RAG should be used.
    return await run_basic_ollama_agent(
        name="create_questions_from_article_agent",
        prompt=prompt,
        server_list=[],
        output_type=list[str],
    )


async def run_single_create_questions_from_article_agent(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the create_questions_from_article agent on the next article in the request status.
    This creates a list of questions from a single article.
    Note that this function expects each article before it to have the exactly correct number of questions.
    """

    # First determine which article to process next.
    num_current_questions = len(request_status.questions)
    questions_per_article = request_status.settings.question_per_article
    next_article_index = num_current_questions // questions_per_article

    if next_article_index >= len(request_status.papers):
        # No more articles to process.
        return request_status, StepInformation(
            warnings=["No more articles to process."]
        )

    # If the number of questions is not a multiple of the number of questions per article,
    # Throw a warning, but progress nontheless.
    # The idea is that the step where the questions are cleaned up will handle this.
    step_info = StepInformation()
    if num_current_questions % questions_per_article != 0:
        step_info.add_warning(
            "The number of questions is not a multiple of the number of questions per article. "
            "This may lead to unexpected results."
        )

    article, _ = request_status.papers[next_article_index]
    # Run the agent on the article.
    questions = await run_create_questions_from_article_agent(
        article, request_status.settings.research_question, questions_per_article
    )
    if questions is None:
        step_info.add_error(
            f"Error creating questions from article {article.title}, skipping."
        )
        return request_status, step_info

    if len(questions) != questions_per_article:
        step_info.add_warning(
            f"Article {article.title} returned {len(questions)} questions, "
            f"but expected {questions_per_article}."
        )

    # Add the questions to the request status.
    for question in questions:
        # The field requires a SurveyQuestion object, so we create it.
        survey_question = SurveyQuestion(
            question=question,
            answer_type=None,  # The type of answer is not known yet, so we set it to None.
            options=None,  # The options for the answer are not known yet, so we set it to None.
        )
        request_status.questions.append(
            (
                survey_question,
                None,  # The relevance score is not known yet, so we set it to None.
            )
        )

    return (request_status, step_info)  # Return the updated request status.


async def run_all_create_questions_from_article_agent(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the create_questions_from_article agent on all articles in the request status.
    This creates a list of questions from each article.
    Note that this expects no article to have been processed yet.
    """
    step_info = StepInformation()

    # If there are no papers, we can't create questions.
    if len(request_status.papers) == 0:
        step_info.add_error("No papers to process.")
        return request_status, step_info

    # Process each article in the request status.
    for article, _ in request_status.papers:
        questions = await run_create_questions_from_article_agent(
            article,
            request_status.settings.research_question,
            request_status.settings.question_per_article,
        )
        if questions is None:
            step_info.add_error(
                f"Error creating questions from article {article.title}, skipping."
            )
            continue

        if len(questions) != request_status.settings.question_per_article:
            step_info.add_warning(
                f"Article {article.title} returned {len(questions)} questions, "
                f"but expected {request_status.settings.question_per_article}."
            )

        # Add the questions to the request status.
        for question in questions:
            survey_question = SurveyQuestion(
                question=question,
                answer_type=None,  # The type of answer is not known yet, so we set it to None.
                options=None,  # The options for the answer are not known yet, so we set it to None.
            )
            request_status.questions.append(
                (
                    survey_question,
                    None,  # The relevance score is not known yet, so we set it to None.
                )
            )

    return (request_status, step_info)  # Return the updated request status.
