### Web Tools (`enhanced_web_tool.py`)

> **bb7_ doctrine:** `bb7_` is not the tool — it compiles a smarter tool. The four `bb7_*` methods here are async orchestrators on top of `aiohttp.ClientSession` and a small set of parsing helpers (`_normalize_url`, `_fetch_web_content`, `_extract_readable_content`, `_analyze_html_structure`, `_perform_web_search`, etc.). The `bb7_*` surface handles argument extraction, URL normalization, content-type detection, response framing, and human-readable formatting; the HTTP, parsing, and download work is delegated. Callers can chain: `bb7_search_web` (find candidate URLs) → `bb7_fetch_url` (extract readable text) → `bb7_analyze_webpage` (SEO/structure deep-dive) → `bb7_download_file` (persist raw asset).

> **Pairing: this file is the `web` router surface named by [`auto-tool-module`](auto-tool-module.md).** `auto-tool-module.py`'s `tool_categories["web"]` references `bb7_fetch_url`, `bb7_download_file`, `bb7_check_url_status`, `bb7_search_web`, and `bb7_extract_links` — but **only four of these are defined in source** (this file: `bb7_fetch_url`, `bb7_search_web`, `bb7_analyze_webpage`, `bb7_download_file`). The remaining two (`bb7_check_url_status`, `bb7_extract_links`) are referenced by the router but are not yet defined; treat them as route stubs and report to the auto-tool-module owner before adding new bb7_ methods. Pair with [`memory-and-mem-interconnect`](memory-and-mem-interconnect.md) (`bb7_memory_store`) to persist fetched content; the local `data/web_cache/` is a fetch cache, not a memory store.

> **Legacy retirement context (2026-06-06):** Earlier doc versions referenced a retired legacy `web_tool.py` and a "legacy retirement rule." There is no separate legacy module in the current source tree; `tools/enhanced_web_tool.py` is the sole web gateway. The historical narrative is preserved above as a warning against introducing a `tools/web_tool.py` to match stale category-map strings.

> **Lisan routing alias — `bb7_web_search`.** `tools/lisan_al_gaib.py:3610`
> declares `"bb7_web_search"` inside its intent-routing data structures
> with a routing score of 0.6 and required param `["query"]`. This is a
> **routing alias**, not a method definition — Lisan maps the alias to
> `bb7_search_web` (this module) during intent resolution. If you grep
> for `def bb7_web_search` in `tools/`, you will not find it.

#### Class & Runtime Configuration

Single class `WebTool` (line 30) hosts all four `bb7_*` methods. Initialization (line 35) configures:

| Config | Value | Notes |
|---|---|---|
| `cache_dir` | `$SOVEREIGN_DATA_DIR/web_cache` | Created with `parents=True, exist_ok=True` on init. |
| `default_timeout` | `30` seconds | Used for `aiohttp.ClientTimeout` in `_get_session`. |
| `max_content_size` | `10 * 1024 * 1024` (10 MB) | Hard ceiling for fetchable content. |
| `user_agent` | Chrome 91 UA string | Faked desktop UA for compatibility. |
| `default_headers` | UA + Accept (HTML/XHTML/XML/WebP), Accept-Language, gzip/deflate, keep-alive, Upgrade-Insecure-Requests | Sent on every request. |
| `supported_content_types` | `text/html`, `text/plain`, `application/json`, `application/xml`, `text/xml`, `application/rss+xml`, `application/atom+xml`, `text/css`, `application/javascript`, `text/javascript` | Allowlist for content-type handling. |
| `search_engines` | `duckduckgo` (https://api.duckduckgo.com/), `github` (https://github.com/search), `stackoverflow` (https://stackoverflow.com/search), `docs` (https://docs.python.org/3/search.html) | URL templates; each `{query}` substituted via `quote_plus`. |
| `session` | `Optional[aiohttp.ClientSession]` | Lazy-created and re-created on event-loop switch (line 80-103). |
| `_session_loop` | `Optional[asyncio.AbstractEventLoop]` | Tracks the loop the session was bound to. |

**Async semantics**: All four `bb7_*` methods are `async def`. They **must** be awaited. The session is per-loop; do not share the `WebTool` instance across event loops without calling `close_session()` first.

**Data dir**: Honors `SOVEREIGN_DATA_DIR` env var (line 25-27). Defaults to `/home/daeron/Somnus-MCP/data`. The cache subdirectory is `web_cache`.

---

#### `bb7_fetch_url`

Fetch any HTTP/HTTPS URL with automatic content-type detection, metadata extraction, optional readable-text extraction, and optional save-to-cache. Returns a structured human-readable report (status, content type, length, fetch time, metadata, content analysis, extracted text, insights, suggested actions).

**Internal Composition**: Orchestrates `_normalize_url()` (scheme-defaults to `https`; rejects malformed), `_fetch_web_content()` (aiohttp GET with `follow_redirects` flag, status/content-type/length/final-url/metadata capture), `_extract_html_metadata()` (title/description/keywords/author/lang), `_analyze_web_content()` (insight generation), `_extract_readable_content()` (HTML→text; truncates to 3000 chars with full-length note when over), `_get_content_insights()` (per-content-type), `_get_action_suggestions()` (follow-up hints), and optionally `_save_cached_content()`. Error branches: `aiohttp.ClientResponseError` → `_analyze_http_error(status)`; `aiohttp.ClientError` → network-error with connection/URL/suggestion; generic `Exception` → `Fetch Error` with the exception string.

- **Parameters**:
  - `url` (string, **required**): HTTP/HTTPS URL. Missing scheme defaults to `https`. Empty string returns "Please provide a URL to fetch."
  - `extract_text` (boolean, optional, default `true`): When `true`, append an "Extracted Content" block (truncated at 3000 chars). When `false`, skips readable extraction.
  - `follow_redirects` (boolean, optional, default `true`): Forwarded to aiohttp. When `false`, the response is the immediate status without the redirect chain.
  - `include_metadata` (boolean, optional, default `true`): When `true`, emits a "Page Metadata" block (title, description (truncated to 200 chars), keywords (first 10), author, lang). When `false`, skipped.
  - `save_content` (boolean, optional, default `false`): When `true`, calls `_save_cached_content()` and emits a "Saved Content: <path>" line.

#### `bb7_search_web`

Search a supported engine and return ranked results with optional snippets, search insights, and related-query generation. Returns "No results found" with suggestions on empty results, or a numbered list with `Search Insights` and `Related Searches` sections on hit.

**Internal Composition**: Orchestrates `_perform_web_search()` (engine-specific GET with `quote_plus` URL templating), `_parse_search_results()` (engine-specific response shape normalization), `_calculate_relevance_score()` (per-result scoring), `_analyze_search_results()` (corpus-level insights from the ranked set), and `_generate_related_queries()` (related-query suggestions). The `search_engine` value must be one of the keys in `self.search_engines`; unknown values return an "Available: ..." error.

- **Parameters**:
  - `query` (string, **required**): Search keywords. Empty string returns "Please provide a search query."
  - `search_engine` (string, optional, default `duckduckgo`): One of `duckduckgo`, `github`, `stackoverflow`, `docs`. Each maps to a different URL template (see config table above).
  - `max_results` (integer, optional, default `10`): Caps the result set size.
  - `include_snippets` (boolean, optional, default `true`): When `true`, each result emits a "Description" line truncated to 300 chars.

#### `bb7_analyze_webpage`

Comprehensive webpage analysis covering structure, links, images, scripts, SEO, technical characteristics, performance, and accessibility. This is the deep-dive companion to `bb7_fetch_url` — same fetch path, but routes through all analysis subsystems.

**Internal Composition**: Orchestrates `_normalize_url()` → `_fetch_web_content()` → `_analyze_html_structure()` (DOM/element analysis) → `_analyze_seo_factors()` (gated on `analyze_seo`) → `_analyze_technical_aspects()` (headers, response characteristics) → `_get_performance_insights()` (load-time/resource signals) → `_analyze_accessibility()` (a11y heuristics). Each `include_*` flag gates one analysis pass; `analyze_seo` is a separate top-level toggle on the SEO pass.

- **Parameters**:
  - `url` (string, **required**): URL of the HTML/XHTML webpage. Required.
  - `include_links` (boolean, optional, default `true`): Run link analysis and emit a "links" section.
  - `include_images` (boolean, optional, default `true`): Run image analysis (alt-text coverage, src patterns, etc.).
  - `include_scripts` (boolean, optional, default `false`): Run script/resource reference analysis. Off by default to keep output focused.
  - `analyze_seo` (boolean, optional, default `true`): Run the SEO factor pass and emit a "SEO" section.

#### `bb7_download_file`

Download any URL to disk with content-type detection, size-limit enforcement, overwrite control, and post-download file analysis + security notes. Returns a structured report including the saved path, size, content type, security check result, and usage suggestions.

**Internal Composition**: Orchestrates `_normalize_url()` → `_get_file_info()` (HEAD-equivalent metadata probe) → `_download_file_content()` (aiohttp GET with streaming, `max_size` enforcement) → `_extract_filename_from_url()` (URL-path or `Content-Disposition` extraction) → `_analyze_downloaded_file()` (post-download content-type sniffing) → `_check_file_security()` (extension/MIME danger patterns) → `_get_file_usage_suggestions()`. Overwrite is enforced on the caller side: when `overwrite=False` and the destination exists, the call returns without writing.

- **Parameters**:
  - `url` (string, **required**): URL of the file/resource. Required.
  - `filename` (string, optional): Custom filename. When omitted, auto-detected from the URL path or `Content-Disposition` header.
  - `destination` (string, optional, default `downloads`): Directory name under the working directory. Created if missing. Relative path.
  - `max_size` (integer, optional, default `104857600` (100 MB)): Hard ceiling for the download in bytes. Files exceeding this are aborted.
  - `overwrite` (boolean, optional, default `false`): When `false`, existing files block the write. When `true`, the existing file is replaced.
