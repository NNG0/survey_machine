# The Base of agents. 

# All agents are represented as a function that is called with specific parameters. 

from typing import Optional, Type, TypeVar
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_ollama import OllamaAugmentedLLM


T = TypeVar("T")
async def run_basic_ollama_agent(name: str, prompt: str, server_list: list[str], custom_llm: Optional[str] = None, output_type: Type[T] = str) -> Optional[T]:
    """ A basic agents that runs a prompt with the default (or specific) LLM and the given MCP servers.
    Args:
        name (str): The name of the agent.
        prompt (str): The prompt to run, already formatted.
        server_list (list[str]): A list of MCP servers to use.
        custom_llm (Optional[str]): A custom LLM to use instead of the default.
        Returns: the response from the agent as type T or None if the agent failed."""

    try: 
        agent = Agent(name=name, instruction=prompt, server_names=server_list)
        async with agent:
            if custom_llm:
                llm = await agent.attach_llm(lambda:
                        OllamaAugmentedLLM( 
                    default_model=custom_llm,
                ))
            else:
                llm = await agent.attach_llm(OllamaAugmentedLLM)
            # llm is now definetly defined. 
            response = await llm.generate_structured(prompt, response_model=output_type)
            return response
    except Exception as e:
        print(f"Error running agent {name}: {e}")
        return None