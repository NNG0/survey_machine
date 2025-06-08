import asyncio
import time
from typing import Awaitable, Callable, Literal, Optional, TypeVar

import httpx

from mcp_agent.app import MCPApp
from mcp_agent.config import LoggerSettings, Settings, MCPSettings, MCPServerSettings, OpenAISettings
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from mcp_agent.workflows.llm.augmented_llm_ollama import OllamaAugmentedLLM
from mcp_agent.logging.logger import Logger

from pydantic import BaseModel

from MCP.agents.check_literature_relevance import run_check_literature_relevance_agent
from MCP.agents.check_question_relevance import run_check_question_relevance_agent
from MCP.agents.create_questions_from_article import run_create_questions_from_article_agent
from MCP.agents.create_survey_question import run_create_survey_question_agent
from MCP.agents.relevant_literature import run_relevant_literature_agent

from MCP.types import RequestStatus

# The mcp_agent.config.yaml file is not working correctly for whatever reason, so instead, it's getting coded here. 

mcp_settings = MCPSettings(
    servers={
        "fetch": MCPServerSettings(
            command="uvx",
            args=["mcp-server-fetch"],
        ),
        "google_scholar" : MCPServerSettings( 
            command="uvx",
            args=["google-scholar-mcp-server"],
        ),
    }
)

openai_settings = OpenAISettings(
    # base_url="http://10.89.0.3:11434/v1", # The ollama virtual machine
    base_url="http://host.docker.internal:11434/v1", # The local ollama server (native is faster on my machine)
    api_key="ollama",
    # The setting of the model using kwargs isn't documented, but it works.
    # default_model="qwen3", # 8b Model
    default_model="qwen3:0.6b", # My memory isn't large enough for 8b, sorry :(
    # default_model="llama3.2", # Trying out a non-reasoning model
    http_client=httpx.Client(timeout=30.0)
)

logger = LoggerSettings(
    # level="debug",
    level="info",
)

# time.sleep(500) # For debugging purposes, this is a long sleep to keep the container running

app = MCPApp(name="hello_world_agent", settings= Settings(mcp=mcp_settings, openai=openai_settings, logger=logger), human_input_callback=None)

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


T = TypeVar("T")
async def try_run_agent(agent_func: Callable[..., Awaitable[T]], num_tries = 3, *args, **kwargs) -> T | None:
    """This function tries to run an agent function a number of times and returns the result if successful.
    If it fails, it returns None.
    """
    result = None
    for i in range(num_tries):
        try:
            result = await agent_func(*args, **kwargs)
        except Exception as e:
            print(f"Error in try_run_agent: {e}")
            time.sleep(1)
        else:
            break # Breaking is a fucking exception in Python, so we need the try-except-else block; breaking inside the try block will not work.

    return result

paper_relevance_threshold = 0.5
question_relevance_threshold = 0.5

async def main_loop(research_question: str):
    """This is the main loop of a request. It takes in the research question and does all the steps to create the survey.
    """


    # Initializing the app
    async with app.run() as mcp_agent_app:


        logger = mcp_agent_app.logger
        logger.info("Starting main loop")

        # The state is an object of type RequestStatus.
        status = RequestStatus(trace_file="MCP/traces/request-" + str(int(time.time())) + ".txt") # The trace file is named with the current timestamp, so it is unique.

        # First set the papers.
        papers = await try_run_agent(
            run_relevant_literature_agent,
            research_question=research_question,
            paper_limit=2, # Just for testing, we limit the number of papers to 2.
        )

        if papers is None:
            print("No relevant papers found, exiting.")
            return None
        
        status.papers = [(paper, None) for paper in papers] # The relevance score is not known yet, so we set it to None.

        # Check their relevance
        for paper in papers:
            relevance = await try_run_agent(
                run_check_literature_relevance_agent,
                article=paper,
                research_question=research_question,
            )
            if relevance is not None:
                status.papers.append((paper, relevance))
            else:
                print(f"Error checking relevance of paper {paper.title}, skipping.")
                continue
        
        # Now we have a list of papers and their relevance scores. Let's filter them.
        status.papers = [paper for paper in status.papers if paper[1] is not None and paper[1] >= paper_relevance_threshold] # Unscoreable papers are not included in the list.
        if len(status.papers) == 0:
            print("No relevant papers found, exiting.")
            return None
        print(f"Relevant papers: {status.papers}")

        # Now we need to create the questions from the papers.

        for paper in status.papers:
            questions = await try_run_agent(
                run_create_questions_from_article_agent,
                article=paper[0],
                research_question=research_question,
            )
            if questions is None:
                print(f"Error creating questions from paper {paper[0].title}, skipping.")
                continue

            # Check the relevance of the questions
            for question in questions:
                relevance = await try_run_agent(
                    run_check_question_relevance_agent,
                    question=question,
                    research_question=research_question,
                )
                if relevance is not None:
                    # The question still needs to be formatted, so we need to run the agent_create_survey_question function.
                    formatted_question = await try_run_agent(
                        run_create_survey_question_agent,
                        question=question,
                        research_question=research_question,
                    )
                    if formatted_question is None:
                        print(f"Error formatting question {question}, skipping.")
                        continue
                    status.questions.append((formatted_question, relevance))
                else:
                    print(f"Error checking relevance of question {question}, skipping.")
                    continue
            
            # Now we have a list of questions and their relevance scores. Let's filter them.
        status.questions = [question for question in status.questions if question[1] is not None and question[1] > question_relevance_threshold]


        # Done for now!
        print(f"Relevant questions: {status.questions}")
        return status




if __name__ == "__main__":
    asyncio.run(main_loop("What is the impact of social media on mental health?"))