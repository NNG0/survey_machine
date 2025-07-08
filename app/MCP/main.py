import asyncio
import time

import httpx
import requests

from mcp_agent.app import MCPApp
from mcp_agent.config import (
    LoggerSettings,
    Settings,
    MCPSettings,
    MCPServerSettings,
    OpenAISettings,
)


from MCP.types import RequestStages, RequestStatus, StepInformation, StatusSetting
from MCP.steps import next_step, run_single_stage


# The mcp_agent.config.yaml file is not working correctly for whatever reason, so instead, it's getting coded here.

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

app = MCPApp(
    name="hello_world_agent",
    settings=Settings(mcp=mcp_settings, openai=openai_settings, logger=logger),
    human_input_callback=None,
)

# Drafting the structure:
# Each agent is modeled as a function that takes in a request and returns a response.
# That way we can limit the capabilities of the agent to only what is needed.


# The first agent needs to take in the research question for the survey and make a plan for what to do.


# The literature agent needs to

# The output agents need to work tegether to create the final latex product.
# Let's assume they at the very end recieve a list of questions and the type of answer the questioned person can give.


# TODO: Add agent that checks whether the research question is valid and if it can be answered with the given literature.
# TODO: Add agent that checks whether the research question is ethical.


# TODO: Maybe create an agent that can work on the questions.

# TODO: Do we use additional memory for the agents?


# TODO: add the output agents


async def old_main_loop(research_question: str):
    """This is the main loop of a request. It takes in the research question and does all the steps to create the survey.
    This time, it uses the stepping system to run the agents."""

    # Initializing the app
    async with app.run() as mcp_agent_app:
        logger = mcp_agent_app.logger
        logger.info("Starting main loop")

        # The state is an object of type RequestStatus.
        status = RequestStatus(
            settings=StatusSetting(
                research_question=research_question,
                paper_limit=2,  # For testing, we limit the number of papers to 2.
            ),
            trace_file="MCP/traces/request-" + str(int(time.time())) + ".txt",
        )  # The trace file is named with the current timestamp, so it is unique.

        stage = next_step(status)
        while stage is not None and stage[3] != RequestStages.FINISHED:
            print(
                stage[0]
            )  # The first element is a human-readable string describing the step.
            # Run a single stage of the request.
            status, step_info = await run_single_stage(status)
            logger.debug(f"Finished stage: {stage[3]}")
            logger.debug(f"Current status: {status}")
            step_info.print_warnings_and_errors()
            # DEBUG
            print(f"Current status: {status}")

            # Lastly, update the stage to the next step.
            stage = next_step(status)

            # We could also run a single step instead.

        # Result:
        print(f"Relevant questions: {status.questions}")
        if stage is None or stage[3] == RequestStages.FINISHED:
            print("All stages finished successfully.")
        else:
            print(f"Last stage: {stage[3]}")


async def new_main_loop(research_question: str):
    """This is the main loop of a request. It takes in the research question and does all the steps to create the survey.
    This time, while it still uses the stepping system, it runs the agents on the hosted server."""

    settings = StatusSetting(
        research_question=research_question,
        paper_limit=2,  # For testing, we limit the number of papers to 2.
    )

    status = RequestStatus(
        settings=settings  # For testing, we limit the number of papers to 2.
    )  # The trace file is named with the current timestamp, so it is unique.

    # DEBUG: send it to the server at the /run_single_next_step endpoint.
    print(f"Initial status: {status.to_dict()}")
    r = requests.get(
        "http://localhost:8001/run_single_next_step",
        json=status.to_dict(),
        headers={"Content-Type": "application/json"},
    )
    if r.status_code != 200:
        print(f"Error: {r.status_code} - {r.text}")
        return
    response = r.json()
    print(f"Response: {response}")
    status = RequestStatus(**response[0])
    step_info = StepInformation(**response[1])
    print(f"Current status: {status}")
    step_info.print_warnings_and_errors()


if __name__ == "__main__":
    import sys

    # print(sys.argv)
    # For now, we can start the server if no arguments are given.
    if len(sys.argv) <= 1:
        print("In order to start the server, please use 'fastapi run MCP/server.py'.")
        exit()
    else:
        # Else, we expect that something happened, for example, a test run.
        if sys.argv[-1] == "test":
            asyncio.run(
                new_main_loop("What is the impact of social media on mental health?")
            )
