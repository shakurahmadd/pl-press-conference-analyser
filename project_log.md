# Project Log — PL Press Conference Analyser

---

## Phase 1 — Data Collection & Validation

### 2026-03-23 — Data Source Discovery

**Decision:** Scrape Arsenal press conferences via Arsenal's Typesense JSON search API rather than parsing static HTML.

**Why:** The Arsenal website loads press conference listings dynamically. The browser makes a POST request to a Typesense search endpoint and renders the JSON response. Calling this API directly from Python gives us clean, structured JSON with no HTML parsing required for the listing layer.

**Alternatives considered:** BeautifulSoup on static HTML — ruled out because the content is dynamically rendered and wouldn't be present in the initial HTML response.

**Trade-offs:** Relying on an undocumented client-side API that Arsenal could change or rate-limit without notice. The API key is a publicly exposed read-only client-side key — acceptable here because it's intentionally embedded in their public JS for browser use, with no write permissions and no billing implications. 

- Save raw JSON per article before loading to SQLite: if one article's data is corrupted or needs reprocessing we just have to touch one file.

**Open questions:**
- Are all 1094 results actually press conferences, or does `category_name` vary? Needs programmatic verification.
- Does the `body` field always contain the full transcript, or sometimes just a summary?
- Is there a rate limit on this endpoint?

**Interview Q I should be able to answer:** Why is it better to call a JSON API directly than scrape rendered HTML?

---

