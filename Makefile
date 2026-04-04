# AI Scraping Stack — Makefile
.PHONY: dev test install clean docker-up docker-down mcp lint format pull-defaults

dev:
	uvicorn api:app --reload --host 0.0.0.0 --port 8100

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src --cov=providers -v

install:
	pip install -r requirements.txt
	scrapling install

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker-compose build

mcp:
	scrapling mcp

mcp-extended:
	python stack.py serve

lint:
	ruff check src/ providers.py api.py stack.py

format:
	ruff format src/ providers.py api.py stack.py

pull-defaults:
	ollama pull llama3.2
	ollama pull mistral
	ollama pull qwen2.5

pull-vision:
	ollama pull qwen2.5vl:7b
	ollama pull llava:7b
	ollama pull moondream
