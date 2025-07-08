from fastapi import FastAPI
import httpx

from MCP.steps import RequestStatus, StepInformation, run_single_next_step

from mcp_agent.app import MCPApp
from mcp_agent.config import (
    LoggerSettings,
    Settings,
    MCPSettings,
    MCPServerSettings,
    OpenAISettings,
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
