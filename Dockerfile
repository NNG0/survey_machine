FROM python:3.13

WORKDIR /app

# Pip but faster
RUN pip install uv

# First, copy only the requirements file to leverage Docker cache
COPY app/requirements.txt ./app/requirements.txt

# Then, install the dependencies
RUN uv pip install --system --no-cache-dir -r ./app/requirements.txt

# Copy the rest of the application code
COPY app/frontend ./app/frontend
COPY app/literature_access ./app/literature_access
COPY app/MCP ./app/MCP
COPY .env /.env

ENV AM_I_IN_DOCKER=true

WORKDIR /app/app
CMD ["fastapi", "run", "MCP/server.py", "--host", "0.0.0.0", "--port", "8001"]
# It's on 8001 to not conflict with the main FastAPI app on port 8000
