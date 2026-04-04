FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi uvicorn[standard] httpx pydantic pydantic-settings python-dotenv \
    scrapling ollama openai

COPY . .

RUN scrapling install

EXPOSE 8100

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8100"]
