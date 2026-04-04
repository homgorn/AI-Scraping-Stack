# SKILL: synthesize_website
# Trigger: "make a website from these URLs", "build site based on X", 
#           "analyze 10 sites and create landing page", "scrape and generate"
# Input: 1-50 URLs + prompt describing desired output
# Output: complete website code (HTML | React | Full-stack spec)

## What this skill does
Multi-agent pipeline:
  1. Scrapes all URLs in parallel (free providers first)
  2. Extractor agent: pulls key patterns from each page
  3. Jina Search: researches current trends for the topic
  4. Ranker agent: filters best insights from all pages
  5. Architect agent: designs site structure + UX approach
  6. Coder agent: generates complete production code

## API call — single output
```
POST http://localhost:8100/synthesize
{
  "urls": ["https://site1.com", "https://site2.com", "...up to 50"],
  "prompt": "Create a SaaS landing page for an AI scraping tool. Dark theme, modern.",
  "output_format": "html",       // html | react | fullstack_spec
  "research_trends": true,       // fetch current trends via Jina Search
  "complexity": "high"           // use best available LLM
}
```

## API call — multiple variants
```
POST http://localhost:8100/synthesize/multi
{
  "urls": ["https://..."],
  "prompt": "...",
  "num_variants": 2              // returns html + react variants
}
```

## Output formats

### html
Complete standalone `<!DOCTYPE html>` file.
- Inline CSS (no external deps)
- CDN JS only if needed (Tailwind CDN, Alpine.js)
- Mobile responsive
- All sections from architect spec

### react
Complete React 18 component.
- Hooks, Tailwind CDN, Lucide icons
- TypeScript JSDoc annotations
- Default export ready for Vite/CRA

### fullstack_spec
Markdown specification including:
- Directory tree
- Tech stack with versions
- Database schema (SQL)
- REST/GraphQL API endpoints
- Docker compose outline
- Estimated dev time per module

## Python usage
```python
from src.synthesizer import WebSynthesizer
from src.config import get_settings
from src.llm import LLMRouter

settings = get_settings()
llm = LLMRouter(settings)
synth = WebSynthesizer(settings, llm)

result = await synth.run(
    urls=["https://competitor1.com", "https://competitor2.com"],
    prompt="Build a B2B SaaS pricing page that converts better than competitors",
    output_format="html",
    research_trends=True,
    complexity="high",
)

print(result.code)      # complete HTML
print(result.insights)  # what agents found valuable
print(result.trends)    # current trends fetched
```

## Prompt guide for best results

### Effective prompts
```
"Create a dark-themed SaaS landing page for AI scraping API. 
Emphasize: free tier, Python SDK, 10x faster than competitors.
Sections: Hero, Features (6), Pricing (3 tiers), API preview, CTA"

"Build a comparison landing page for developer tools.
Include: benchmark table, code examples, migration guide from X to Y"

"Generate a product page for [product].
Target audience: senior developers. Technical tone. Dark mode."
```

### URL selection strategy
- 3-5 URLs: curated top competitors or references
- 10-20 URLs: broad landscape analysis (sitemap pages, product pages)
- 50 URLs: comprehensive research (use for fullstack_spec output)

## Agent pipeline (internal)

```
URLs → [Scraper x N parallel]
     ↓
[Extractor agent x N parallel] ← analyzes each page separately
     ↓
[Jina Search] ← fetches trends (2 queries)
     ↓
[Ranker agent] ← synthesizes all extractions into top 15 insights
     ↓
[Architect agent] ← designs structure, stack, UX
     ↓
[Coder agent] ← generates final code
     ↓
SynthesisResult { code, insights, trends, spec, stack }
```

## Cost estimate
| # URLs | Complexity | Approx cost | Time |
|--------|-----------|-------------|------|
| 5      | low (Ollama) | $0.00 | 30-60s |
| 20     | medium (OR free) | $0.00 | 60-120s |
| 50     | high (Claude) | ~$0.10 | 2-5min |

## Output fields
- `code` — generated website code
- `html` — same as code if format=html
- `spec` — architect's JSON design spec
- `stack` — recommended tech stack
- `insights` — top patterns found in scraped URLs
- `trends` — current trends from Jina Search
- `urls_processed` — how many URLs succeeded
- `elapsed_ms` — total pipeline time
- `cost_usd` — estimated cost
