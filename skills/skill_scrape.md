# SKILL: scrape_and_analyze
# Trigger: "scrape X", "get content from URL", "analyze website", "extract data from"
# Input: URL + optional task
# Output: text/JSON analysis

## What this skill does
Fetches a URL using the best available provider (cascade: Jina → Scrapling → httpx),
then analyzes the content with local Ollama or OpenRouter.

## API call
```
POST http://localhost:8100/scrape
{
  "url": "<URL>",
  "strategy": "smart",          // free | fast | smart | stealth | premium
  "task": "summarize",          // summarize | extract_entities | classify | extract_prices | sentiment | qa:<question> | custom:<instruction>
  "complexity": "low",          // low=Ollama | medium=OR-free | high=OR-paid
  "css_selector": "",           // optional CSS selector for targeted extraction
  "mode": "fast"                // fast | stealth (Cloudflare) | dynamic (JS-heavy)
}
```

## Strategy selection guide
| Site type | Strategy |
|-----------|----------|
| Simple static | `free` (Jina) |
| Regular site | `smart` (cascade) |
| Cloudflare protected | `stealth` |
| JS SPA | `dynamic` |
| Need best quality | `premium` (Firecrawl) |

## Task selection guide
| Goal | Task |
|------|------|
| Summary for humans | `summarize` |
| People, orgs, dates | `extract_entities` |
| Product/price pages | `extract_prices` |
| News/blog/docs | `classify` |
| Tone of content | `sentiment` |
| Specific question | `qa:What is the main price?` |
| Custom extraction | `custom:List all phone numbers` |

## Python usage
```python
from providers import ProviderRouter
from src.config import get_settings

router = ProviderRouter({"jina_api_key": get_settings().jina_api_key})
result = await router.scrape("https://example.com", strategy="smart")
print(result.markdown)   # clean text ready for LLM
```

## Jina shortcut (zero setup)
```bash
curl https://r.jina.ai/https://example.com
```
Returns clean markdown, no API key needed (rate limited to ~20 RPM).

## Output fields
- `markdown` — clean LLM-ready text
- `text` — plain text
- `html` — raw HTML
- `title` — page title
- `analysis` — LLM output for chosen task
- `model_used` — which model was used
- `cost_usd` — estimated cost
- `elapsed_ms` — total time
- `provider` — which provider was used

## Error handling
If `error` field is set, all providers failed. Check:
1. URL is accessible
2. Try `strategy="stealth"` for protected sites
3. Add `SCRAPERAPI_KEY` in `.env` for last-resort fallback
