# Footer Cache & Session — Real Provider Sources

## MiniMax (M2.7)
Field: `response.usage.prompt_tokens_details.cached_tokens`
Formula: `cached_tokens / prompt_tokens * 100`
Example API response:
```json
"usage": {
  "prompt_tokens": 11,
  "completion_tokens": 10,
  "total_tokens": 21,
  "prompt_tokens_details": {"cached_tokens": 0},
  "completion_tokens_details": {"reasoning_tokens": 10}
}
```

## DeepSeek (V4 Flash)
No cache metric exposed in current runtime. Cache: UNKNOWN.
Do not use MiniMax cached_tokens data for DeepSeek footers.

## OpenRouter
Config has `response_cache: true` with `response_cache_ttl: 300`.
Metadata may contain cache hit info in response headers.

## Hermes Config Settings
- `prompt_caching.cache_ttl: 5m` — configured but not observed in API response yet
- `openrouter.response_cache: true` — OpenRouter response caching

## Session % — Preflight Compression
When session exceeds threshold, system emits:
```
📦 Preflight compression: ~N tokens >= M threshold.
```
- N = current session token count
- M = threshold (default ~102,400)
- Session % = N / M * 100
- 100%+ = force compact on next message
- If you see this in user message → extract N and M, compute %
- Source: actual preflight message in session context

## General Rule
Cache % = `cached_tokens / prompt_tokens * 100`
If field absent or provider doesn't expose → UNKNOWN
Never reuse cache data across different providers.
