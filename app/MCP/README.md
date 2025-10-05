# Backend

The backend of the survey machine serves a FastAPI server to fulfill requests.
It serves the MCP server as well as the connection to the database for papers and workflows.

## Setup

To start the backend, simply create a `.env` file in the top directory, next to the `.env.example` file, where the necessary fields can be seen.

It can then be started with all other containers using docker-(or podman-)compose.

## MCP Server

The MCP Server doesn't itself serve a MCP Server, but uses MCP to answer requests from the clients
using a "Client-Only-State Model", where the client itself holds all data and may call the server for help.

### Client-Only-State Model

The COSM is new model I wrote for this project, as no other model fulfills the requirements of this projects (Stateless/State-based CRDTs come close, but don't have the focus on the client).

The main idea is that the client holds the entire state and can edit (almost) all of it freely (exceptions for IDs and update-at fields).
The state holds a single project with key questions, papers, settings and the final markdown draft and includes many fields.
The user may edit these fields and thus work on the state by themselves, but may also, on demand, make a request to the server
to edit the state in some predefined way.
The server then sends back the updated state, which is shown to the user immeadeatly.

For this to work, both client and server need to agree on the state model and the client may not modify the state while the server modifies it.

This model gives the user very granular control over the state, as they may directly edit the state or let an AI do some work and then fix the AI's work.

### MCP Agents

To actually modify the state, a bunch of different agents are created for different, specific tasks.

| Agent Name                | Purpose                                                                                                          | When It Runs                                                                    | Which field it modifies                           |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------- |
| **Create Key Questions**  | Generates key research questions based on the main research question                                             | After the papers were parsed, if no key questions exist yet                     | `key_questions`                                   |
| **Relevant Literature**   | Finds and retrieves relevant academic papers based on the research question using OpenAlex                       | At the beginning of the workflow, if the list of papers is empty                | `papers`                                          |
| **Parse Papers**          | Extracts problem questions and research methods from each paper's title and abstract (and content, if available) | After papers are retrieved, if some paper isn't parsed yet                      | `papers[].problem_questions`, ` papers[].methods` |
| **Adjust Key Questions**  | Assigns specific papers to key questions by matching question relevance to paper content                         | After key questions are created and papers are parsed                           | `key_questions[].1`                               |
| **Extract Results**       | Analyzes papers assigned to each key question and extracts research findings and results                         | After key questions are assigned to papers, processes questions without results | `key_questions[].2`                               |
| **Create Draft Headings** | Creates a structured outline with markdown headings for the final literature review                              | After key questions and results are available, if no draft headings exist yet   | `drafts[].title`                                  |
| **Fill Draft Content**    | Writes the actual content for each section heading using the research findings                                   | At the end, after the draft headings were generated                             | `drafts[].content`                                |

Each agent is independent and can be configured by itself.

Additionally, each agent can either be run to run a single time, or to run the entire stage. For example, if the agent for adjusting the key questions were told to run the entire stage (`/run_all_adjust_questions`), it would adjust all key questions, instead of only a single one.

### next_step

To simplify the workflow for the user, and to prevent a misclick from putting a project into an inconvenient state by calling the wrong agent, the `next_step` system and function is built on top of the COSM with MCP agents.

The `next_step` function on the backend takes in the state and returns a human readable string of what the next step will be, as well as the name of the functions/agents to call to either run a single step, or the entire stage.
The stage is an Enum that describes how far the project is currently. Each stage corresponds to the agent to call next, except the last one, which signifies that the project is considered finished.

# Further work

As with all projects, backend can also always be expanded, but there are a few obvious improvements that could be made in the future:

- Implement dedicated buttons on the frontend for each agent: Currently, for simplicity, the frontend can only access the backend using the `next_step` function via the "Execute Next Step" button. Ideally, the user should be allowed to also call each agent, though this would run into the problem that agents are not always adequate to call, depending on the state. (Maybe the backend should also send which agents are currently available/good to call?)
- Focus agents' editing fields: each agent only edits a specific field in the state, which is also known beforehand. Instead of having to lock the entire state to avoid "merge conflicts" (see State-based CRDTs), only the field that is currently being edited by the LLM needs to be locked. This will also launching multiple LLMs concurrently for a single project.
- Allow agents to work on a specific index: currently, if an agent is run in "single" mode, it searches for the next index it needs to work on. Thus, there is currently no way to tell it to work on a specific index. This would somewhat break the COSM, but could maybe be done using a new optional field `parameters` in the `RequestStatus`, next to the settings.
