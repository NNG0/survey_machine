import asyncio
import os
import time

from mcp_agent.app import MCPApp
from mcp_agent.config import LoggerSettings, Settings, MCPSettings, MCPServerSettings, OpenAISettings
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

# The mcp_agent.config.yaml file is not working correctly for whatever reason, so instead, it's getting coded here. 

mcp_settings = MCPSettings(
    servers={
        "fetch": MCPServerSettings(
            command="uvx",
            args=["mcp-server-fetch"],
        ),
    }
)

openai_settings = OpenAISettings(
    # base_url="http://10.89.0.3:11434/v1", # The ollama virtual machine
    base_url="http://host.docker.internal:11434/v1", # The local ollama server (native is faster on my machine)
    api_key="ollama",
    # default_model="qwen3", # 8b Model
    # default_model="qwen3:4b", # My memory isn't large enough for 8b, sorry :(
    default_model="llama3.2", # Trying out a non-reasoning model
)

logger = LoggerSettings(
    # level="debug",
    level="info",
)

# time.sleep(500) # For debugging purposes, this is a long sleep to keep the app running

app = MCPApp(name="hello_world_agent", settings= Settings(mcp=mcp_settings, openai=openai_settings, logger=logger))

# stopper = time.sleep(500) # Keep the app running for 500 seconds

async def example_usage():
    async with app.run() as mcp_agent_app:
        logger = mcp_agent_app.logger

        # This agent can read the filesystem or fetch URLs
        finder_agent = Agent(
            name="finder",
            instruction="""You can read local files or fetch URLs.
                Return the requested information when asked.""",
            server_names=["fetch"], # MCP servers this Agent can use
        )

        async with finder_agent:
            # Automatically initializes the MCP servers and adds their tools for LLM use
            tools = await finder_agent.list_tools()
            # logger.info(f"Tools available:", data=tools)

            # Attach an OpenAI LLM to the agent (I set it to use the qwen3 model by default)
            llm = await finder_agent.attach_llm(OpenAIAugmentedLLM)

            # Uses the fetch server to fetch the content from URL
            result = await llm.generate_str(
                message="Print the first two paragraphs from https://www.anthropic.com/research/building-effective-agents"
            )
            logger.info(f"Blog intro: {result}")

            # Multi-turn interactions by default
            result = await llm.generate_str(
                message="Summarize that in a 128-char tweet", 
            )
            logger.info(f"Tweet: {result}")

if __name__ == "__main__":
    asyncio.run(example_usage())
