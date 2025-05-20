import asyncio
import os
import time
from typing import Awaitable, Callable, Literal, TypeVar

from mcp_agent.app import MCPApp
from mcp_agent.config import LoggerSettings, Settings, MCPSettings, MCPServerSettings, OpenAISettings
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from mcp_agent.workflows.llm.augmented_llm_ollama import OllamaAugmentedLLM
from mcp_agent.logging.logger import Logger

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

app = MCPApp(name="hello_world_agent", settings= Settings(mcp=mcp_settings, openai=openai_settings, logger=logger), human_input_callback=None)



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
        llm = await scholar_agent.attach_llm(OllamaAugmentedLLM)

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

        generated_citation = await run_scholar_structured(input="Use Google Scholar to get the content of the paper with the URL: " + url_list[0] +" and create a summary of the Articles with their title, abstract, author and URL.", response_type=Article)
        logger.info(f"Generated citation: {generated_citation}")



# Try to get it to create an article
class Article(BaseModel):
    title: str | None
    author: str | None
    abstract: str | None
    url: str | None



# Drafting the structure:
# Each agent is modeled as a function that takes in a request and returns a response. 
# That way we can limit the capabilities of the agent to only what is needed.


# The first agent needs to take in the research question for the survey and make a plan for what to do. 


# The literature agent needs to 


# The output agents need to work tegether to create the final latex product. 
# Let's assume they at the very end recieve a list of questions and the type of answer the questioned person can give. 


class SurveyQuestion(BaseModel):
    question: str
    answer_type: Literal["Text"] | Literal["Multiple choice"] | Literal["Yes/No"] | Literal["Range"] # The type of answer the questioned person can give. For example, "text", "multiple choice", "yes/no" or a "out of a range from x to y...". # TODO: Add more types of answers?
    options: list[str] | tuple[int, int] | Literal["Text field"] # The options for the answer, if applicable. For example, ["yes", "no"] for a yes/no question.
    

class RequestStatus:
    """This class is used to track the status of a single request over the lifetime of the server.
    It stores all data needed to track the request and is meant to represent the progress.
    It can also be stored and loaded due to this."""

    papers: list[tuple[Article, float | None]] # The list of papers and their relevance scores

    questions: list[tuple[SurveyQuestion, float | None]] # The list of questions and their relevance scores

    def pretty_print(self):
        """Prints the status of the request in a human-readable format."""
        print(f"Request status: {self.__dict__}") # TODO: Add a better pretty print function

    # By overriding the __setattr__ method, we can make sure that the status is always printed when it is updated.
    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        # Pretty print the status when it is updated.
        if name == "papers" or name == "questions":
            self.pretty_print()

    # Besides the setattr, we can also override the __getattr__ method for the few times where the papers or questions are modified.
    def __getattr__(self, name):
        # First make sure that it's only done for the papers and questions.
        if name == "papers" or name == "questions":
            self.pretty_print()
        return super().__getattr__(name) # The linter is complaining, is this correct?
    

# TODO: Add agent that checks whether the research question is valid and if it can be answered with the given literature.
# TODO: Add agent that checks whether the research question is ethical.

async def agent_relevant_literature(research_question: str, paper_limit: int) -> list[Article] | None:
    """This agent receives the research question and returns a list of relevant literature."""

    try:
        prompt = f"""
    You are a research assistant. Given a research question, you need to find relevant literature.
    You have access to Google Scholar to look up papers. For the research question, find the most relevant papers and return a list of articles with their title, abstract, author and URL.
    Limit the number of articles to {paper_limit}.
    research question: {research_question}""" # TODO: Add examples on how to do this, multi-shot learning is important
        
        agent = Agent(
            name="relevant_literature",
            instruction=prompt,
            server_names=["googleScholar"], # MCP servers this Agent can use
        )
        async with agent:
            # Attaches the LLM to the agent
            llm = await agent.attach_llm(OllamaAugmentedLLM)

            # Uses the input to generate a structured response
            result = await llm.generate_structured(
                message=prompt,
                response_model=list[Article],
            )
            return result
    except Exception as e:
        print(f"Error in agent_relevant_literature: {e}")
        return None


async def agent_check_literature_relevance(article: Article, research_question: str) -> float | None:
    """This agent receives an article and a research question and returns an estimated relevance score for the article between 0 and 1.
    The higher the score, the more relevant the article is to the research question.
    """

    try:
        prompt = f"""
You are a professional research assistant. Given a research question and an article, you need to estimate the relevance of the article to the research question.
Only based on the title, abstract and author of the article, return a score between 0 and 1 for the relevance of the article to the research question.

research question: {research_question}

Article: {article.title} by {article.author}
Abstract: {article.abstract}
"""
        agent = Agent(
            name="check_literature_relevance",
            instruction=prompt,
        )
        async with agent:
            # Attaches the LLM to the agent
            llm = await agent.attach_llm(OllamaAugmentedLLM)

            # Uses the input to generate a structured response
            result = await llm.generate_structured(
                message=prompt,
                response_model=float,
            )
            return result
    except Exception as e:
        print(f"Error in agent_check_literature_relevance: {e}")
        return None
    

async def agent_create_questions_from_article(article: Article, research_question: str) -> list[str] | None:
    """This agent receives an article and a research question and returns a list of questions to ask the surveytakers. 
    They are supposed to be open-ended and not correctly formatted yet. 
    """

    try:
        prompt = f"""
You are a professional research assistant. There will be a survey about the aricle you will recieve.
Based on the content of the article, create a list of questions that, when answered in the survey, will help answer the question.
Return the questions in a list format.
Research question: {research_question}.
Article: {article.title} by {article.author}
Abstract: {article.abstract}""" # TODO: Here, both few-shot and RAG should be used.
        agent = Agent(
            name="create_questions_from_article",
            instruction=prompt,
        )
        async with agent:
            # Attaches the LLM to the agent
            llm = await agent.attach_llm(OllamaAugmentedLLM)

            # Uses the input to generate a structured response
            result = await llm.generate_structured(
                message=prompt,
                response_model=list[str],
            )
            return result
    except Exception as e:
        print(f"Error in agent_create_questions_from_article: {e}")
        return None
    

async def agent_check_question_relevance(question: str, research_question: str) -> float | None:
    """This agent receives a question and a research question and returns an estimated relevance score for the question between 0 and 1.
    The higher the score, the more relevant the question is to the research question.
    """

    try:
        prompt = f"""
You are a professional research assistant. Given a research question and another question, which will be asked in a survey, you need to estimate the relevance of the question to the research question.
Only based on the content of the question, return a score between 0 and 1 for the relevance of the question to the research question.
Research question: {research_question}
Question: {question}""" 
        agent = Agent(
            name="check_question_relevance",
            instruction=prompt,
        )
        async with agent:
            # Attaches the LLM to the agent
            llm = await agent.attach_llm(OllamaAugmentedLLM)

            # Uses the input to generate a structured response
            result = await llm.generate_structured(
                message=prompt,
                response_model=float,
            )
            return result
    except Exception as e:
        print(f"Error in agent_check_question_relevance: {e}")
        return None


async def agent_create_survey_question(question: str, research_question: str) -> SurveyQuestion | None:
    """This agent receives a question and the main research question and returns a correctly formatted survey question."""
    try:
        prompt = f"""
        You are a professional research assistant. You will be creating a survey for a research question.
        Given a question, you need to think ybout how it will be answered and output correctly formatted survey question."""

        agent = Agent(
            name="create_survey_question",
            instruction=prompt,
        )
        async with agent:
            # Attaches the LLM to the agent
            llm = await agent.attach_llm(OllamaAugmentedLLM)

            # Uses the input to generate a structured response
            result = await llm.generate_structured(
                message=prompt,
                response_model=SurveyQuestion,
            )
            return result
    except Exception as e:
        print(f"Error in agent_create_survey_question: {e}")
        return None

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
        status = RequestStatus()

        # First set the papers.
        papers = await try_run_agent(
            agent_relevant_literature,
            research_question=research_question,
            paper_limit=5,
        )

        if papers is None:
            print("No relevant papers found, exiting.")
            return None
        
        status.papers = [(paper, None) for paper in papers] # The relevance score is not known yet, so we set it to None.

        # Check their relevance
        for paper in papers:
            relevance = await try_run_agent(
                agent_check_literature_relevance,
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
                agent_create_questions_from_article,
                article=paper[0],
                research_question=research_question,
            )
            if questions is None:
                print(f"Error creating questions from paper {paper[0].title}, skipping.")
                continue

            # Check the relevance of the questions
            for question in questions:
                relevance = await try_run_agent(
                    agent_check_question_relevance,
                    question=question,
                    research_question=research_question,
                )
                if relevance is not None:
                    # The question still needs to be formatted, so we need to run the agent_create_survey_question function.
                    formatted_question = await try_run_agent(
                        agent_create_survey_question,
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