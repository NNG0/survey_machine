# The Base of agents.

# All agents are represented as a function that is called with specific parameters.

from typing import Tuple, Type, TypeVar, Union
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_ollama import OllamaAugmentedLLM
from datetime import datetime

import re
import traceback

T = TypeVar("T")


async def run_basic_ollama_agent[T](
    name: str,
    prompt: str,
    server_list: list[str],
    output_type: Type[T] = str,
) -> Union[T, Tuple[bool]]:
    """A basic agents that runs a prompt with the default (or specific) LLM and the given MCP servers.
    Args:
        name (str): The name of the agent.
        prompt (str): The prompt to run, already formatted.
        server_list (list[str]): A list of MCP servers to use.
        Returns: the response from the agent as type T, (false,) if the agent failed and (true,) if the agent hit a rate limit."""

    # If the rate limit was less than one minute ago, immeadiately fail with rate limit error
    if (
        last_rate_limit_time
        and (datetime.now() - last_rate_limit_time).total_seconds() < 60
    ):
        return (True,)

    try:
        agent = Agent(name=name, instruction=prompt, server_names=server_list)

        async with agent:
            llm = await agent.attach_llm(OllamaAugmentedLLM)
            # llm is now definitely defined.

            # if the T typevar is str:
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
                if isinstance(response, Exception):
                    print(f"Error: {response}")
                    return (False,)
                return response
            else:
                response = await llm.generate_structured(
                    prompt, response_model=output_type
                )
                if isinstance(response, Exception):
                    print(
                        f"Error running agent {name}: {response}; {traceback.format_exc()}"
                    )
                    return (False,)
                # elif isinstance(response, output_type): # It seems that we cannot do this, because in the case of list[str], isinstance does not work. (That is a parameterized generic type)
                return response
                # else:
                #     print(
                #         f"Error: Agent {name} returned unexpected type {type(response)}"
                #     )
                #     return (False,)
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
