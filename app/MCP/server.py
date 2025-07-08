from fastapi import FastAPI
import httpx

from MCP.steps import (
    RequestStatus,
    StepInformation,
    run_single_next_step,
    run_single_stage,
    run_until_before_stage,
    next_step,
)


from MCP.types import RequestStages

from mcp_agent.app import MCPApp
from mcp_agent.config import (
    LoggerSettings,
    Settings,
    MCPSettings,
    MCPServerSettings,
    OpenAISettings,
)

from MCP.agents.check_literature_relevance import (
    run_single_check_literature_relevance_agent,
    run_all_check_literature_relevance_agent,
)
from MCP.agents.check_question_relevance import (
    run_all_check_question_relevance_agent,
    run_single_check_question_relevance_agent,
)
from MCP.agents.create_survey_question import (
    run_single_create_survey_question_agent,
    run_all_create_survey_questions_agent,
)
from MCP.agents.relevant_literature import (
    run_all_relevant_literature_agent,
    run_single_relevant_literature_agent,
)
from MCP.agents.create_questions_from_article import (
    run_all_create_questions_from_article_agent,
    run_single_create_questions_from_article_agent,
)


# A simple server that runs the MCP agents.
# Basically, it will support the `steps.py` file and the `agents` folder.


mcp_settings = MCPSettings(
    servers={
        "fetch": MCPServerSettings(
            command="uvx",
            args=["mcp-server-fetch"],
        ),
        "google_scholar": MCPServerSettings(
            command="uvx",
            args=["google-scholar-mcp-server"],
        ),
    }
)

openai_settings = OpenAISettings(
    # base_url="http://10.89.0.3:11434/v1", # The ollama virtual machine
    # base_url="http://host.docker.internal:11434/v1",  # The local ollama server (native is faster on my machine)
    base_url="http://localhost:11434/v1",  # The ollama server running on the host machine
    api_key="ollama",
    # The setting of the model using kwargs isn't documented, but it works.
    # default_model="qwen3", # 8b Model
    default_model="qwen3:0.6b",  # My memory isn't large enough for 8b, sorry :(
    # default_model="llama3.2", # Trying out a non-reasoning model
    http_client=httpx.Client(timeout=30.0),
)

logger = LoggerSettings(
    # level="debug",
    # level="info",
    level="warning",  # Set to warning to avoid too much output
)

# time.sleep(500) # For debugging purposes, this is a long sleep to keep the container running

mcp_app = MCPApp(
    name="hello_world_agent",
    settings=Settings(mcp=mcp_settings, openai=openai_settings, logger=logger),
    human_input_callback=None,
)


# with mcp_app.run() as mcp_agent_app:
app = FastAPI()


@app.get("/run_single_next_step")
async def run_single_step(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run a single step in the request status."""
    step_info = StepInformation()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running single next step for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_single_next_step(request_status)
        return request_status, step_info


@app.get("/next_step")
async def next_step_endpoint(
    request_status: RequestStatus,
) -> tuple[str, str, str, RequestStages] | None:
    """This endpoint is a bit weirder because the python interface returns a tuple of the step name in human readable format, single step function, all steps function, and the stage.
    But the functions are returned as Callables, so we need to return the names of the functions, or rather, the endpoints that are used to run the steps."""
    step = next_step(request_status)
    if step is None:
        return None
    single_fun_name = step[1].__name__  # The name of the single step function
    all_fun_name = step[2].__name__  # The name of the all
    return (
        step[0],  # The name of the step
        single_fun_name,  # The name of the single step function
        all_fun_name,  # The name of the all steps function
        step[3],  # The stage of the step
    )


@app.get("/run_single_stage")
async def run_single_stage_endpoint(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run all steps in the request status for this single stage."""
    step_info = StepInformation()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running single stage for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_single_stage(request_status)
        return request_status, step_info


@app.get("/run_until_before_stage")
async def run_until_before_stage_endpoint(
    request_status: RequestStatus,
    stage: RequestStages,  # The stage to run until before
) -> tuple[RequestStatus, StepInformation]:
    """Run all steps in the request status until the specified stage is reached."""
    step_info = StepInformation()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running until before stage {stage} for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_until_before_stage(request_status, stage)
        return request_status, step_info


# Now, all individual agent steps are defined here.


@app.get("/run_single_check_literature_relevance")
async def run_single_check_literature_relevance(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the single check literature relevance agent."""
    step_info = StepInformation()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running single check literature relevance for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_single_check_literature_relevance_agent(
            request_status
        )
        return request_status, step_info


@app.get("/run_all_check_literature_relevance")
async def run_all_check_literature_relevance(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the all check literature relevance agent."""
    step_info = StepInformation()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running all check literature relevance for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_all_check_literature_relevance_agent(
            request_status
        )
        return request_status, step_info


@app.get("/run_single_check_question_relevance")
async def run_single_check_question_relevance(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the single check question relevance agent."""
    step_info = StepInformation()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running single check question relevance for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_single_check_question_relevance_agent(
            request_status
        )
        return request_status, step_info


@app.get("/run_all_check_question_relevance")
async def run_all_check_question_relevance(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the all check question relevance agent."""
    step_info = StepInformation()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running all check question relevance for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_all_check_question_relevance_agent(
            request_status
        )
        return request_status, step_info


@app.get("/run_single_create_survey_question")
async def run_single_create_survey_question(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the single create survey question agent."""
    step_info = StepInformation()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running single create survey question for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_single_create_survey_question_agent(
            request_status
        )
        return request_status, step_info


@app.get("/run_all_create_survey_questions")
async def run_all_create_survey_questions(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the all create survey questions agent."""
    step_info = StepInformation()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running all create survey questions for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_all_create_survey_questions_agent(
            request_status
        )
        return request_status, step_info


@app.get("/run_single_relevant_literature")
async def run_single_relevant_literature(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the single relevant literature agent."""
    step_info = StepInformation()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running single relevant literature for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_single_relevant_literature_agent(
            request_status
        )
        return request_status, step_info


@app.get("/run_all_relevant_literature")
async def run_all_relevant_literature(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the all relevant literature agent."""
    step_info = StepInformation()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running all relevant literature for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_all_relevant_literature_agent(
            request_status
        )
        return request_status, step_info


@app.get("/run_single_create_questions_from_article")
async def run_single_create_questions_from_article(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the single create questions from article agent."""
    step_info = StepInformation()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running single create questions from article for request: {request_status.settings.research_question}"
        )
        (
            request_status,
            step_info,
        ) = await run_single_create_questions_from_article_agent(request_status)
        return request_status, step_info


@app.get("/run_all_create_questions_from_article")
async def run_all_create_questions_from_article(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the all create questions from article agent."""
    step_info = StepInformation()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running all create questions from article for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_all_create_questions_from_article_agent(
            request_status
        )
        return request_status, step_info
