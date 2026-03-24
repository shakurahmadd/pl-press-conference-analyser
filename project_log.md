# Project Log — PL Press Conference Analyser

---

## Phase 1 — Data Collection & Validation

### 2026-03-23 — Phase 1: Data Source & Scraper

#### What I did
- Discovered Arsenal website uses a Typesense JSON search API via DevTools Network tab
- Inspected POST request payload and response structure
- Set up Git repository and project folder structure
- Built scraper in `src/scraping/scraper.py`
- Scraped 483 unique Arsenal press conferences (January 2018 — March 2026) saved as raw JSON files in `data/raw/`
- Created a script to validate the data in `src/scraping/validate_data.py`
- Checked if any files were missing their "body" 
- Checked the average, min and max length of the files' bodies

#### Key decisions
**Decision:** Scrape via Arsenal's Typesense JSON search API rather than parsing static HTML.

**Why:** The Arsenal website loads press conference listings dynamically. The browser makes a POST request to a Typesense search endpoint and renders the JSON response. Calling this API directly from Python gives us clean, structured JSON with no HTML parsing required for the listing layer.

**Alternatives considered:** BeautifulSoup on static HTML — ruled out because the content is dynamically rendered and wouldn't be present in the initial HTML response.

**Trade-offs:** Relying on an undocumented client-side API that Arsenal could change or rate-limit without notice. The API key is a publicly exposed read-only client-side key — acceptable because it's intentionally embedded in their public JS for browser use, with no write permissions and no billing implications. Saving raw JSON per article before loading to SQLite means slightly more scraper complexity, but if one article's data is corrupted or needs reprocessing we only touch one file.

**Open questions:**
- Does the `body` field always contain the full transcript, or sometimes just a summary? - some of the files contain other infomation or genral articles so will have to be filtered
- Is there a rate limit on this endpoint? - No issues at 5 pages with 10 second delay
- Total pages hardcoded at 5 — should be made dynamic using `found` from the response.

**Interview Q I should be able to answer:** Why is it better to call a JSON API directly than scrape rendered HTML?

---

**Decision:** Filtered out files with less than 200 words. 

**Why:** The files below the threshold did not contain transcripts, but instead were general articles. We do not need these files. 

**Alternatives considered:** Attempted to filter using the "every word" substring, however, there were too many title variations that it did not catch, removing plenty of good data. 

**Trade-offs:** Some files may still contain text that is not transcript related. 

**Open questions:**
- Does the `body` field of full transcripts still include unwanted content 

**Interview Q I should be able to answer:** How did you filter out unneeded files? And how did you decide on the threshold?

---

## Phase 2 — Load Files to Database

### 2026-03-24 — Phase 2: Load Files to Database

#### What I did
- Created a database folder to hold `load_to_db.py`
- BeautifulSoup cleaning approach — removing <a> tags, using separator and strip
- Clean HTML before storing vs storing raw
- The script takes the JSON files -> cleans the html body and loads it into an SQLite database


#### Key decision
**Decision:** Store the data in an SQLite database

**Why:** SQLite databases are good at filtering data. It can be queried directly with SQL - filter by date, by manager, by keyword - without loading all 481 rows into memory first.  

**Alternatives considered:** Using CSV files, however it requres loading everything into pandas or Python before filtering.

**Trade-offs:** CSV files can be opened in Excel or viewed directly, SQLite requires a tool or code to inspect. We also loose some simplicity (setting up connections, cursors...)

**Open questions:**
- Does the cleaned body text still contain any unwanted content beyond <a> tags?
- Does querying the database work? 


**Interview Q I should be able to answer:** Why did you decide to use an SQLite database over a CSV file?


--- 