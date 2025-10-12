# Survey Machine

The survey machine is a project that was made to help draft survery papers and write them in basic markdown.
A single docker compose file orchestrates all necessary containers and exposes a port (by default `4200`) on which the frontend can be accessed.

The frontend gives the user the ability to search for, upload and manage stored papers and articles and create projects that then reference those.
The structure of a project can be edited manually by the user, but they may, at any point, request assistance from an LLM, which will execute the next step in the process.

By default, the GWDG's AI inference is used, for which the environment key needs to be set, see below.

# How to run

Make sure there is a `.env` file that contains at least the `GWDG_API_KEY`, or reconfigure to use a different endpoint.

Then execute the command:

```shell
sudo docker compose up --build
```

## Preparations

While docker is supposed to just work, it is often misconfigured.
For everything to actually run, the docker engine must first be started.
Then, if the computer was restarted recently, the file at `~/.docker/config.json` must be edited to say `credStore` instead of `credsStore` (Yes, really).

By default, the `qwq-32` model is used, but instead, any of the other models the GWDG supports can be used: [see here](https://docs.hpc.gwdg.de/services/chat-ai/models/index.html).
This is configured in the `.env` file. For adjustment, for example which endpoint to use, check out the `.env.example` file.

### 🔧 GROBID Setup (External Service)

Our project uses [**GROBID**](https://github.com/kermitt2/grobid) for PDF parsing.  
GROBID is an external Java-based service that must be running before the application can process PDFs.

**Option 1:** Run GROBID with Docker

```bash
docker run -t --rm -p 8070:8070 lfoppiano/grobid:latest
```

**Option 2:** Run it locally from source  
Follow the setup guide in the [GROBID GitHub repository](https://github.com/kermitt2/grobid#installing-and-running).

Make sure the GROBID service is available at `http://localhost:8070` before starting the app.

### Relevance Scoring with SciBERT

For computing the relevance score of research papers, we use SciBERT, a transformer model trained on scientific text.
This approach is independent of database providers and therefore works both for literature retrieved via APIs (e.g., OpenAlex) and for locally uploaded PDFs.
Each paper’s title and abstract are compared to the current research question to assess its relevance.

The model runs locally (CPU) by default and does not require external API keys, ensuring consistent scoring across environments.

### Test run of MCP

A test run of the MCP functionality can be done by running `uv run -m MCP.main test`.

# Folder structure

All code is within the `app` folder, which, inside the docker container is at `/app` and is the working directory.
Each module (Database, Frontend Interface, MCP, etc.) has its own folder.
The content of the folder doesn't matter and is up to the person adminestering it.
Each folder should, if possible, only have one person working on it at a time to make merge conflicts less likely.

## Git etiquette

To make our lives easier and merge conflict less likely, everyone should only work on their personal branch.
Once they believe their branch is stable enough, they can merge it into main, without deleting the source branch.
(That also means that technically each folder can be treated like a sub-repository)
