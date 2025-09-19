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
COPY .env /.env

# Erstelle das Database-Verzeichnis und setze Berechtigungen
RUN mkdir -p /app/app/database && \
    chmod 755 /app/app/database

ENV AM_I_IN_DOCKER=true
ENV DATABASE_PATH=/app/app/database

WORKDIR /app/app
CMD ["uvicorn", "MCP.server:app", "--host", "0.0.0.0", "--port", "8001"]