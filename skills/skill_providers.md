# SKILL: provider_selection
# Trigger: "which provider", "cheapest way to scrape", "bypass Cloudflare", 
#           "scrape 1000 pages", "protected site", cost optimization
# Input: scraping requirements
# Output: optimal provider selection

## Decision tree
```
Is it a simple static page?
  YES → strategy="free" (Jina Reader, zero cost, zero setup)
  NO → continue

Is JS rendering needed?
  YES → mode="dynamic" or strategy="stealth"
  NO → continue

Is it Cloudflare protected?
  YES → mode="stealth" (Scrapling StealthyFetcher)
  NO → strategy="smart" (Jina → Scrapling → httpx cascade)

Need LLM-ready markdown for RAG?
  YES → strategy="llm" (Crawl4AI)
  NO → strategy="fast" (Scrapling)

Need prompt → JSON extraction?
  YES → strategy="ai" (ScrapeGraphAI + Ollama)
  NO → default flow

Need best possible quality, don't mind cost?
  YES → strategy="premium" (Firecrawl)
```

## Providers comparison table

| Provider | Type | Cost | JS | Anti-bot | Markdown | Setup |
|----------|------|------|----|----|---|---|
| Jina Reader | API | FREE* | ✓ | partial | ✓✓ | None |
| Scrapling | Local | FREE | ✓ | ✓✓ | ✗ | pip |
| Crawl4AI | Local | FREE | ✓ | partial | ✓✓✓ | pip |
| ScrapeGraphAI | Local | FREE** | ✓ | partial | ✗ | pip |
| Scrapingdog | API | $0.0002/req | ✓ | ✓ | ✗ | Key |
| ZenRows | API | $0.0003/req | ✓ | ✓ | ✓ | Key |
| ScraperAPI | API | $0.0005/req | ✓ | ✓✓ | ✗ | Key |
| Scrape.do | API | $29/mo flat | ✓ | ✓ | ✗ | Key |
| Firecrawl | API | $0.002/page | ✓ | ✓ | ✓✓✓ | Key |
| Bright Data | API | $1.50/1K | ✓ | ✓✓✓ | ✗ | Enterprise |

*Jina: free without key (20 RPM), 10M tokens free with key
**ScrapeGraphAI: needs local LLM (Ollama)

## Cost calculation for 1000 pages
```
Free options:     $0.00  (Jina + Scrapling + Crawl4AI)
Scrapingdog:      $0.20
ZenRows:          $0.28
ScraperAPI:       $0.49
Scrape.do:        ~$1.00 (at $29/mo)
Firecrawl:        $2.00
Bright Data:      $1.50
```

## Cascade setup in .env
```env
# Free tier first (Jina)
JINA_API_KEY=jina_...   # optional, raises rate limit

# Paid fallback (only used when Jina + Scrapling fail)
SCRAPERAPI_KEY=...      # 1000 free/mo, then $49/mo
```

## Strategy → provider mapping
```python
strategies = {
    "free":    ["jina", "crawl4ai"],
    "fast":    ["scrapling_fast"],
    "smart":   ["jina", "scrapling_fast", "crawl4ai", "scraperapi"],
    "llm":     ["crawl4ai"],          # best LLM-ready markdown
    "ai":      ["scrapegraphai"],     # prompt → structured JSON
    "premium": ["firecrawl", "crawl4ai"],
    "stealth": ["scrapling_stealth", "scrapingdog", "scraperapi_premium"],
}
```

## For high-volume (10k+ pages/day)
1. Use Scrapling locally (unlimited, free)
2. Add residential proxy rotation:
   ```env
   PROXY_URL=http://user:pass@proxy.brightdata.com:22225
   ```
3. Crawl4AI for async batches (built-in rate limiting)
4. ScraperAPI as last resort

## Install optional providers
```bash
# Crawl4AI (self-hosted, best LLM output)
pip install crawl4ai && crawl4ai-setup

# Firecrawl Python SDK
pip install firecrawl-py

# ScrapeGraphAI + Ollama (semantic extraction)
pip install scrapegraphai
ollama pull llama3.2
```
