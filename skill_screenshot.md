# SKILL: screenshot_and_vision (March 2026)

## Free vision models

### Ollama local
| Model | Pull | VRAM |
|-------|------|------|
| qwen3-vl:30b | ollama pull qwen3-vl:30b | 20GB |
| qwen3-vl | ollama pull qwen3-vl | 6GB |
| qwen2.5vl:7b | ollama pull qwen2.5vl:7b | 6GB |
| llava:7b | ollama pull llava:7b | 6GB |
| moondream | ollama pull moondream | 1.5GB CPU-ok |

From HuggingFace GGUF:
```bash
ollama pull hf.co/Qwen/Qwen3-VL-30B-A3B-Instruct-GGUF:qwen3vl-30b-a3b-instruct-q4_k_m.gguf
```
Or via API: POST /models/ollama/install-hf (SSE stream, auto-registers)

### OpenRouter free (key required)
- qwen/qwen3-vl-235b-a22b-thinking:free  — Best, MoE 235B, design→code
- qwen/qwen3-vl-30b-a3b:free             — Fast bulk
- nvidia/nemotron-nano-2-vl-12b:free     — #1 OCR, charts, docs
- moonshotai/kimi-vl-a3b-thinking:free   — 131K context
- qwen/qwen2.5-vl-72b-instruct:free      — Stable fallback
- meta-llama/llama-3.2-11b-vision-instruct:free
- openrouter/auto                         — auto-picks best free

Auto-refresh: POST /models/vision/refresh

### HuggingFace Inference Providers (HF_TOKEN, ~200/day free)
endpoint: https://router.huggingface.co/v1/chat/completions  (OpenAI-compat)
Search: GET /models/hf/search?q=vision+language

## API endpoints
```
POST /screenshot              single URL → screenshot_b64
POST /screenshot/bulk         N URLs parallel + optional VLM tasks
POST /screenshot/audit        sitemap→key pages→screenshots→VLM
GET  /sitemap?url=            robots.txt + sitemap.xml discovery
POST /vision/analyze          analyze screenshot_b64 with VLM
GET  /models/vision           list all models
POST /models/vision/add       add custom model (OR/Ollama/HF/endpoint)
DELETE /models/vision/{id}    remove custom model
POST /models/vision/refresh   auto-fetch new free OR models
POST /models/ollama/install-hf pull GGUF from HuggingFace
GET  /models/hf/search        search HF for VL models
```

## Vision tasks
business_intel, design_audit, competitor_analysis, tech_stack,
ux_patterns, ocr_extract, content_extract, summary, custom

## Add model examples
```json
# OpenRouter
{"id": "qwen/qwen3-vl-235b-a22b-thinking:free", "name": "Qwen3-VL 235B", "provider": "openrouter"}

# Ollama
{"id": "qwen3-vl:30b", "name": "Qwen3-VL 30B", "provider": "ollama"}

# HuggingFace
{"id": "Qwen/Qwen3-VL-30B-A3B-Instruct", "hf_id": "Qwen/Qwen3-VL-30B-A3B-Instruct",
 "name": "Qwen3-VL HF", "provider": "huggingface"}

# Custom vLLM/llama.cpp server
{"id": "my-vision", "name": "Local vLLM", "provider": "custom_endpoint",
 "base_url": "http://localhost:8000/v1", "api_key": "none", "models": ["qwen3-vl"]}
```

## Env vars
HF_TOKEN=hf_...           (huggingface.co/settings/tokens, free)
OPENROUTER_API_KEY=sk-or-v1-...
