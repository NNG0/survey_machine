FROM python:3.13

WORKDIR /app

# Pip but faster
RUN pip install uv

# First, copy only the requirements file to leverage Docker cache
COPY app/requirements.txt ./app/requirements.txt

# Then, install the dependencies
RUN uv pip install --system --no-cache-dir -r ./app/requirements.txt

# Copy the rest of the application code
COPY app ./app

WORKDIR /app/app
CMD ["uv", "run", "-m", "MCP.main"]
