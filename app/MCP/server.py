import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx

from .steps import (
    RequestStatus,
    StepInformation,
    run_single_next_step,
    run_single_stage,
    run_until_before_stage,
    next_step,
)


from .types import RequestStages

from mcp_agent.app import MCPApp
from mcp_agent.config import (
    LoggerSettings,
    Settings,
    MCPSettings,
    MCPServerSettings,
    OpenAISettings,
)

from .agents.relevant_literature import (
    run_all_relevant_literature_agent,
    run_single_relevant_literature_agent,
)

from .agents.adjust_key_questions import (
    run_all_adjust_questions_agent,
    run_single_adjust_questions_agent,
)

from .agents.create_key_questions import (
    run_all_create_key_questions_agent,
    run_single_create_key_questions_agent,
)

from .agents.extract_results import (
    run_all_extract_results_agent,
    run_single_extract_results_agent,
)

from .agents.parse_papers import (
    run_all_parse_papers_agent,
    run_single_parse_papers_agent,
)

# A simple server that runs the MCP agents.
# Basically, it will support the `steps.py` file and the `agents` folder.

literature_access_url = (
    "http://localhost:8000/mcp"  # The URL of the literature access server
)
if os.getenv("AM_I_IN_DOCKER", "false") == "true":
    literature_access_url = (
        "http://literature-access:8000/mcp"  # Access over the shared network
    )

mcp_settings = MCPSettings(
    servers={
        "fetch": MCPServerSettings(
            command="uvx",
            args=["mcp-server-fetch"],
        ),
        "literature_access": MCPServerSettings(
            transport="streamable_http",
            url=literature_access_url,
        ),
    }
)


def get_openai_settings():
    """Create OpenAI settings with a new AsyncClient for each request."""
    is_in_docker = os.getenv("AM_I_IN_DOCKER", "false") == "true"
    if is_in_docker:
        base_url = "http://host.docker.internal:11434/v1"  # The local ollama server from within docker (native is faster on some machines including mine)
        # base_url="http://ollama-instance:11434/v1",  # The ollama server running inside docker (docker handles DNS)
        pass
    else:
        base_url = "http://127.0.0.1:11434/v1"  # The ollama address when running without docker

    # If the GWDG api key is found in the .env file, use that endpoint instead
    import dotenv

    dotenv.load_dotenv()
    gwdg_api_key = os.getenv("GWDG_API_KEY")
    if gwdg_api_key:
        base_url = "https://chat-ai.academiccloud.de/v1"
        default_model = "qwen3-32b"
        # default_model = "qwen3-235b-a22b"
    else:
        # default_model = "qwen3:0.6b"
        default_model = "qwen3:4b"

    # Do a quick ping to that address to make sure it works (without "/v1")
    try:
        response = httpx.get(f"{base_url[:-3]}")
        response.raise_for_status()
    except httpx.HTTPError as e:
        print(f"Error pinging ollama server: {e}, are you sure it is running?")

    return OpenAISettings(
        base_url=base_url,  # The selected ollama address
        api_key=gwdg_api_key or "ollama",
        http_client=httpx.AsyncClient(timeout=30.0),  # type: ignore (The library is weird and doesn't mention that this needs to be set.)
        default_model=default_model,  # type: ignore
    )


logger = LoggerSettings(
    # level="debug",
    # level="info",
    level="warning",  # Set to warning to avoid too much output
)

# time.sleep(500) # For debugging purposes, this is a long sleep to keep the container running


def create_mcp_app():
    """Create a new MCPApp instance with properly initialized async client."""
    return MCPApp(
        name="hello_world_agent",
        settings=Settings(
            mcp=mcp_settings, openai=get_openai_settings(), logger=logger
        ),
        human_input_callback=None,
    )


# with mcp_app.run() as mcp_agent_app:
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/run_single_next_step")
async def run_single_step(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run a single step in the request status."""
    step_info = StepInformation()
    mcp_app = create_mcp_app()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running single next step for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_single_next_step(request_status)
        return request_status, step_info


@app.post("/next_step")
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
    mcp_app = create_mcp_app()
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
    mcp_app = create_mcp_app()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running until before stage {stage} for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_until_before_stage(request_status, stage)
        return request_status, step_info


# Now, all individual agent steps are defined here.


@app.get("/run_single_relevant_literature")
async def run_single_relevant_literature(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the single relevant literature agent."""
    step_info = StepInformation()
    mcp_app = create_mcp_app()
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
    mcp_app = create_mcp_app()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running all relevant literature for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_all_relevant_literature_agent(
            request_status
        )
        return request_status, step_info


@app.get("/run_single_adjust_questions")
async def run_single_adjust_questions(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the single adjust questions agent."""
    step_info = StepInformation()
    mcp_app = create_mcp_app()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running single adjust questions for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_single_adjust_questions_agent(
            request_status
        )
        return request_status, step_info


@app.get("/run_all_adjust_questions")
async def run_all_adjust_questions(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the all adjust questions agent."""
    step_info = StepInformation()
    mcp_app = create_mcp_app()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running all adjust questions for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_all_adjust_questions_agent(request_status)
        return request_status, step_info


@app.get("/run_single_create_key_questions")
async def run_single_create_key_questions(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the single create key questions agent."""
    step_info = StepInformation()
    mcp_app = create_mcp_app()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running single create key questions for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_single_create_key_questions_agent(
            request_status
        )
        return request_status, step_info


@app.get("/run_all_create_key_questions")
async def run_all_create_key_questions(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the all create key questions agent."""
    step_info = StepInformation()
    mcp_app = create_mcp_app()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running all create key questions for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_all_create_key_questions_agent(
            request_status
        )
        return request_status, step_info


@app.get("/run_single_extract_results")
async def run_single_extract_results(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the single extract results agent."""
    step_info = StepInformation()
    mcp_app = create_mcp_app()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running single extract results for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_single_extract_results_agent(
            request_status
        )
        return request_status, step_info


@app.get("/run_all_extract_results")
async def run_all_extract_results(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the all extract results agent."""
    step_info = StepInformation()
    mcp_app = create_mcp_app()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running all extract results for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_all_extract_results_agent(request_status)
        return request_status, step_info


@app.get("/run_single_parse_papers")
async def run_single_parse_papers(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the single parse papers agent."""
    step_info = StepInformation()
    mcp_app = create_mcp_app()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running single parse papers for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_single_parse_papers_agent(request_status)
        return request_status, step_info


@app.get("/run_all_parse_papers")
async def run_all_parse_papers(
    request_status: RequestStatus,
) -> tuple[RequestStatus, StepInformation]:
    """Run the all parse papers agent."""
    step_info = StepInformation()
    mcp_app = create_mcp_app()
    async with mcp_app.run() as mcp_agent_app:
        mcp_agent_app.logger.info(
            f"Running all parse papers for request: {request_status.settings.research_question}"
        )
        request_status, step_info = await run_all_parse_papers_agent(request_status)
        return request_status, step_info
