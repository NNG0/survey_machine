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

Then, because the ollama container is not by default enabled, ollama needs to be installed locally and have the `qwen3:4b` model installed (by `ollama pull qwen3b:4b`).

The default ollama model is currently `qwen3:4b` and is defined in the `main.py` where the OpenAI settings are set up.
