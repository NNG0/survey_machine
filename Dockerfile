FROM python:3.13

WORKDIR /app

# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Pip but faster
RUN pip install uv 

RUN uv pip install --system --no-cache-dir -r ./app/requirements.txt

CMD ["python", "./app/main.py"]
