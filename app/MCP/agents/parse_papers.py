from pydantic import BaseModel
from .base import run_basic_ollama_agent
from ..types import RequestStatus, StepInformation


# This class is necessary because pydantic doesn't allow tuples.
class ParsedPaper(BaseModel):
    """Model for the output of parsing a paper to extract problem questions and methods."""

    problem_questions: list[str]
    methods: list[str]


async def run_single_parse_papers_agent(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the parse papers agent on the request status to extract the problem questions and methods from the papers."""
    step_info = StepInformation()

    # First find the next paper to parse.
    paper_to_parse_and_index = next(
        (
            (paper, index)
            for index, paper in enumerate(request_status.papers)
            if paper.problem_questions is None or paper.methods is None
        ),
        None,
    )

    if paper_to_parse_and_index is None:
        step_info.add_warning("No papers to parse.")
        return request_status, step_info  # No more papers to parse.

    paper_to_parse, paper_index = paper_to_parse_and_index

    # Now we can run the agent on the selected paper. It needs to return the problem questions and methods.

    prompt = f"""
    You are a research assistant. Given a paper, you need to extract the few key questions that were asked as well as the methods used to investigate the problem.
    Paper title: {paper_to_parse.article.title}
    Paper abstract: {paper_to_parse.article.abstract}
    Paper URL: {paper_to_parse.article.url}

    Return the problem questions and methods as structured data.
    """

    response = await run_basic_ollama_agent(
        name="parse_paper",
        prompt=prompt,
        output_type=ParsedPaper,
        server_list=["literature_access", "fetch"],
    )

    if response is not None and isinstance(response, ParsedPaper):
        paper_to_parse.problem_questions = response.problem_questions
        paper_to_parse.methods = response.methods
        request_status.papers[paper_index] = paper_to_parse
    elif isinstance(response, Exception):
        step_info.add_error(f"Failed to parse paper at index {paper_index}: {response}")
        print(f"Error: {response}")
        print(f"Debug: {paper_to_parse}")
        print(f"Debug: {request_status}")
    else:
        step_info.add_warning("Failed to parse paper.")

    return request_status, step_info


async def run_all_parse_papers_agent(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the parse papers agent on all papers in the request status."""
    step_info = StepInformation()

    tries_at_this_index = 0
    last_tried_index = -1

    index = 0

    while index < len(request_status.papers):
        if tries_at_this_index >= 3:
            step_info.add_warning(
                f"Failed to parse paper at index {index} after 3 attempts."
            )
            index += 1
            continue

        paper = request_status.papers[index]
        if index == last_tried_index:
            tries_at_this_index += 1
        else:
            tries_at_this_index = 1
        last_tried_index = index

        if paper.problem_questions is None or paper.methods is None:
            # If the paper has not been parsed yet, run the parsing agent.
            status, info = await run_single_parse_papers_agent(request_status)
            step_info.merge(info)
            step_info.add_warning(f"Failed to parse paper at index {index}.")
            if status is not None:
                request_status = status

    return request_status, step_info
