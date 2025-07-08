import asyncio

import requests


from MCP.types import RequestStages, RequestStatus, StepInformation, StatusSetting


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

    # print(f"Initial status: {status.to_dict()}")

    stage = requests.get(
        "http://localhost:8001/next_step",
        json=status.to_dict(),
    )
    while (
        stage.status_code == 200  # All responses should be 200 OK
        and stage.json()  # The json should be valid
        and stage.json()[3]
        != RequestStages.FINISHED  # And the request should not be finished
    ):
        response = stage.json()
        print(response[0])  # Print the human-readable message:
        r = requests.get(
            "http://localhost:8001/run_single_next_step",  # Try to run the next step
            json=status.to_dict(),
            headers={"Content-Type": "application/json"},
        )
        if r.status_code != 200:
            print(f"Error: {r.status_code} - {r.text}")
            return
        response = r.json()

        # Debug?
        print(f"Response: {response}")

        status = RequestStatus(**response[0])
        step_info = StepInformation(**response[1])

        print(f"Current status: {status}")
        step_info.print_warnings_and_errors()

        # Get the next step
        stage = requests.get(
            "http://localhost:8001/next_step",
            json=status.to_dict(),
        )


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
