# The Base of agents.

# All agents are represented as a function that is called with specific parameters.

from typing import Optional, Tuple, Type, TypeVar, Union
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_ollama import OllamaAugmentedLLM
from datetime import datetime

from ..types import SupportedProviders

import re
import traceback

T = TypeVar("T")


async def run_basic_ollama_agent(
    name: str,
    prompt: str,
    server_list: list[str],
    custom_provider: Optional[SupportedProviders] = None,
    output_type: Type[T] = str,
) -> Union[T, Tuple[bool]]:
    """A basic agents that runs a prompt with the default (or specific) LLM and the given MCP servers.
    Args:
        name (str): The name of the agent.
        prompt (str): The prompt to run, already formatted.
        server_list (list[str]): A list of MCP servers to use.
        custom_provider (Optional[SupportedProvider]): The provider to use, if any. If None, the default Ollama provider is used.
        Returns: the response from the agent as type T, (false,) if the agent failed and (true,) if the agent hit a rate limit."""

    # If the rate limit was less than one minute ago, immeadiately fail with rate limit error
    if (
        last_rate_limit_time
        and (datetime.now() - last_rate_limit_time).total_seconds() < 60
    ):
        return (True,)

    try:
        agent = Agent(name=name, instruction=prompt, server_names=server_list)
        # print("Agent created successfully.")
        async with agent:
            # print("Agent context opened successfully.")
            # if custom_provider:
            #     # print(f"Attaching custom provider: {custom_provider.get_provider}")
            #     llm = await agent.attach_llm(custom_provider.get_provider)
            # else:
            # print("Attaching default OllamaAugmentedLLM.")
            llm = await agent.attach_llm(OllamaAugmentedLLM)
            # llm is now definetly defined.
            # print("LLM attached successfully.")
            if output_type is str:
                # The output type is string, don't force the llm to output in a specific format
                response = await llm.generate_str(prompt)

                # The response can be empty to signal a 429 rate limit. In that case, we'll set the last rate limit to now
                # and return the info that a rate limit was hit.

                if response == "":
                    handle_rate_limit()
                    return (True,)

                if isinstance(response, str):
                    # We need to post-process the response, as it could contain <think> tags.
                    response = post_process_response_string(response)
            else:
                response = await llm.generate_structured(
                    prompt, response_model=output_type
                )
            # print("Response generated successfully.")
            return response  # type: ignore This complains about the type because the type system of python cannot express this.
    except Exception as e:
        print(f"Error running agent {name}: {e}; {traceback.format_exc()}")
        return (False,)


def post_process_response_string(response: str) -> str:
    """Post-process the response string to remove any <think> tags and their content."""
    # Remove <think>...</think> tags and their content
    cleaned_response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)
    return cleaned_response.strip()


last_rate_limit_time = None


def handle_rate_limit():
    global last_rate_limit_time
    last_rate_limit_time = datetime.now()
