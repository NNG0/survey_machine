# The Base of agents.

# All agents are represented as a function that is called with specific parameters.

from typing import Optional, Type, TypeVar
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_ollama import OllamaAugmentedLLM

from MCP.types import SupportedProviders

import traceback

T = TypeVar("T")


async def run_basic_ollama_agent(
    name: str,
    prompt: str,
    server_list: list[str],
    custom_provider: Optional[SupportedProviders] = None,
    output_type: Type[T] = str,
) -> Optional[T]:
    """A basic agents that runs a prompt with the default (or specific) LLM and the given MCP servers.
    Args:
        name (str): The name of the agent.
        prompt (str): The prompt to run, already formatted.
        server_list (list[str]): A list of MCP servers to use.
        custom_provider (Optional[SupportedProvider]): The provider to use, if any. If None, the default Ollama provider is used.
        Returns: the response from the agent as type T or None if the agent failed."""

    # DEBUG: remove all print statements below.

    try:
        agent = Agent(name=name, instruction=prompt, server_names=server_list)
        # print("Agent created successfully.")
        async with agent:
            # print("Agent context opened successfully.")
            if custom_provider:
                # print(f"Attaching custom provider: {custom_provider.get_provider}")
                llm = await agent.attach_llm(custom_provider.get_provider)
            else:
                # print("Attaching default OllamaAugmentedLLM.")
                llm = await agent.attach_llm(OllamaAugmentedLLM)
            # llm is now definetly defined.
            # print("LLM attached successfully.")
            response = await llm.generate_structured(prompt, response_model=output_type)
            # print("Response generated successfully.")
            return response
    except Exception as e:
        print(f"Error running agent {name}: {e}; {traceback.format_exc()}")
        return None
