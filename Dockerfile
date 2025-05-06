FROM python:3.13

WORKDIR /app

# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# Pip but faster
RUN pip install uv 

COPY app ./app

RUN uv pip install --system --no-cache-dir -r ./app/requirements.txt

CMD ["uv", "run", "./app/main.py"]
