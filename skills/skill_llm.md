# SKILL: llm_routing
# Trigger: "analyze text", "summarize", "extract", "which model", "add model", "use Claude/GPT"
# Input: text + task + complexity preference
# Output: analysis from best available model

## Routing logic
```
complexity="low"   → Ollama local (llama3.2, mistral, qwen)  FREE, private
complexity="medium" → OpenRouter free tier                     FREE, cloud
complexity="high"   → OpenRouter configured model              PAID, best quality
```

Fallback: if Ollama offline → OpenRouter free tier.
If no OpenRouter key → always Ollama.

## API call
```
POST http://localhost:8100/analyze?task=summarize&model_source=auto
body: text=<raw text>
```

Or via scrape endpoint with complexity param:
```json
{"url": "...", "task": "summarize", "complexity": "medium"}
```

## Available tasks
```
summarize          → 3-5 sentence summary
extract_entities   → JSON: people, orgs, dates, prices
classify           → one word: news/product/blog/docs/ecommerce
extract_prices     → JSON: [{name, price, available}]
sentiment          → JSON: {positive, negative, neutral, label}
extract_links      → JSON: [{url, text}]
translate_ru       → Russian translation
translate_en       → English translation
qa:<question>      → answer from text
custom:<prompt>    → any instruction
```

## Add models

### Ollama (local, free)
```bash
ollama pull mistral          # 4.1GB, great for extraction
ollama pull qwen2.5          # 4.4GB, multilingual
ollama pull deepseek-r1      # reasoning tasks
ollama pull phi3             # lightweight, fast
```
Or via API: `POST /models/ollama/pull {"model_name": "mistral"}`

### OpenRouter custom model
```
POST /models/openrouter
{"model_id": "x-ai/grok-2", "name": "Grok 2", "free": false, "tier": "high"}
```

### Custom OpenAI-compatible API
```
POST /models/api
{
  "name": "Groq",
  "base_url": "https://api.groq.com/openai/v1",
  "api_key": "gsk_...",
  "models": ["llama3-70b-8192", "mixtral-8x7b-32768"],
  "description": "Ultra-fast inference"
}
```

### Prebuilt presets in dashboard
Groq, Together.ai, Perplexity, DeepInfra, Fireworks, Anyscale

## Free OpenRouter models (updated March 2026)
```
qwen/qwen3-30b-a3b:free               High quality, multilingual
meta-llama/llama-3.3-70b-instruct:free  Best free quality
deepseek/deepseek-r1:free             Best for reasoning
google/gemini-2.0-flash-exp:free      Fast, Google
mistralai/mistral-nemo:free           Balanced
microsoft/phi-3-mini-128k-instruct:free  Lightweight
```
Full list: https://openrouter.ai/models?max_price=0

## Python usage
```python
from src.llm import LLMRouter
from src.config import get_settings

llm = LLMRouter(get_settings())

# Low: Ollama local
result = await llm.analyze("text here", task="summarize", complexity="low")

# Medium: OpenRouter free tier
result = await llm.analyze("text", task="extract_entities", complexity="medium")

# Override to specific model
result = await llm.analyze("text", task="summarize",
    model_override="qwen/qwen3-30b-a3b:free")

print(result.analysis)
print(result.model_used)
print(result.elapsed_ms)
```
