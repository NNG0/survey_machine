import asyncio
import os
import time

from mcp_agent.app import MCPApp
from mcp_agent.config import LoggerSettings, Settings, MCPSettings, MCPServerSettings, OpenAISettings
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

from pydantic import BaseModel

# The mcp_agent.config.yaml file is not working correctly for whatever reason, so instead, it's getting coded here. 

mcp_settings = MCPSettings(
    servers={
        "fetch": MCPServerSettings(
            command="uvx",
            args=["mcp-server-fetch"],
        ),
        "googleScholar" : MCPServerSettings( 
            command="uvx",
            args=["google-scholar-mcp-server"],
        ),
    }
)

openai_settings = OpenAISettings(
    # base_url="http://10.89.0.3:11434/v1", # The ollama virtual machine
    base_url="http://host.docker.internal:11434/v1", # The local ollama server (native is faster on my machine)
    api_key="ollama",
    # default_model="qwen3", # 8b Model
    default_model="qwen3:4b", # My memory isn't large enough for 8b, sorry :(
    # default_model="llama3.2", # Trying out a non-reasoning model
)

logger = LoggerSettings(
    # level="debug",
    level="info",
)

# time.sleep(500) # For debugging purposes, this is a long sleep to keep the container running

app = MCPApp(name="hello_world_agent", settings= Settings(mcp=mcp_settings, openai=openai_settings, logger=logger))

async def run_scholar_structured(input: str, response_type):
    """Runs the defined agent with capability to access Google Scholar and returns the result. 
    The output is a structured object, so it can be used to create a citation or other structured data.
    """

    scholar_agent = Agent(
        name="scholar",
        instruction="""You can access Google Scholar, looking up papers, their citations and their content.
            Return the requested information when asked.""",
        server_names=["googleScholar"], # MCP servers this Agent can use
    )

    async with scholar_agent:
        # Attaches the LLM to the agent
        llm = await scholar_agent.attach_llm(OpenAIAugmentedLLM)

        # Uses the input to generate a structured response
        result = await llm.generate_structured(
            message=input,
            response_model=response_type,
        )
        return result


async def example_usage():
    async with app.run() as mcp_agent_app:
        logger = mcp_agent_app.logger

        # Because of a bug in the mcp-agent, it cannot call a tool multiple times, so we first ask it to generate the URLs. 
        # (It'll be fixed in the next minor release)
        url_list = await run_scholar_structured(
            input="Use Google Scholar to find the latest research paper by Gretchen McCulloch and return the URLs of the first 5 papers",
            response_type=list[str],
        )

        logger.info(f"Generated URLs: {url_list}")
        print(f"Generated URLs: {url_list}")
        assert len(url_list) > 0, "Expected at least one URL"

        # Try to get it to create an article
        class Article(BaseModel):
            title: str | None
            author: str | None
            abstract: str | None
            url: str | None

        generated_citation = await run_scholar_structured(input="Use Google Scholar to get the content of the paper with the URL: " + url_list[0] +" and create a summary of the Articles with their title, abstract, author and URL.", response_type=Article)
        logger.info(f"Generated citation: {generated_citation}")


if __name__ == "__main__":
    asyncio.run(example_usage())
