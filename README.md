# Folder structure

All code is within the `app` folder, which, inside the docker container is at `/app` and is the working directory.
Each module (OpenAlex, BERTopic, Frontend Interface, MCP, etc.) has its own folder.
The content of the folder doesn't matter and is up to the person adminestering it.
Each folder should, if possible, only have one person working on it at a time to make merge conflicts less likely.

(MCP integration is very simple, don't think too much about it, We can talk about it further later.)

## Git etiquette

To make our lives easier and merge conflict less likely, everyone should only work on their personal branch.
Once they believe their branch is stable enough, they can merge it into main, without deleting the source branch.
(That also means that technically each folder can be treated like a sub-repository)

# How to run

```shell
sudo docker compose up --build
```

Note that the uv library is used instead of pip, so the building can be done at the very end of the Dockerfile.
If you need any new libraries that are pip-compatible, just throw them into requirements, the load time is currently still under three seconds.

If you need node or other non-python stuff, write Sebastian; that will be quite a hassle to get into docker.

## Preparations

While docker is suppoed to just work, it is often misconfigured.
For everything to actually run, the docker engine must first be started.
Then, if the pc was restarted recents, the file at `~/.docker/config.json` must be edited to say `credStore` instead of `credsStore` (Yes, really).

Then, because the ollama container is not by default enabled, ollama needs to be installed locally and have the `qwen3:4b` model installed (by `ollama pull qwen3:4b`).

The default ollama model is currently `qwen3:4b` and is defined in the `main.py` where the OpenAI settings are set up.

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
