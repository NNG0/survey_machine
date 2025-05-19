FROM python:3.13

WORKDIR /app

# Pip but faster
RUN pip install uv

COPY app ./app

RUN uv pip install --system --no-cache-dir -r ./app/requirements.txt

CMD ["uv", "run", "./app/MCP/main.py"]
