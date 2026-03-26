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

**Alternatives considered:** Using CSV files, however it requires loading everything into pandas or Python before filtering.

**Trade-offs:** CSV files can be opened in Excel or viewed directly, SQLite requires a tool or code to inspect. We also loose some simplicity (setting up connections, cursors...)

**Open questions:**
- Does the cleaned body text still contain any unwanted content beyond <a> tags?
- Does querying the database work? 


**Interview Q I should be able to answer:** 
- Why did you use SQLite over a proper database like PostgreSQL? SQLIte is severless and file based - no setup, no separate process, perfect for a project this size. PostgreSQL is for multi-user, high-concurrent systems.
- Walk me though your HTML cleaning process - why did you specifically remove <a> tags, and what else might you have missed? We used beautiful soup to clean the HTML. final_all was used to find all the text with the HTML link tag <a> and then .decompose to remove it from the body. There might still be text that is not links but filler infomation or introductions. 
- Your created field is stored as a Unix timestamp. How would you query all press conferences from 2023? SELECT * FROM arsenal WHERE created BETWEEN 1672531200 AND 1704067199. We can use datetime module for conversions. 

--- 

## Phase 3 — Selecting and Testing a Baseline Model

#### What I did
- Searched hugging face for sentiment analysis model
- Also checked for any football or sports related ones -> No reliable ones were found
- Selected Twitter-RoBERTa-base-sentiment as a baseline model
- Model has a 512 token limit so we will chunk transcripts into sections, analyse each chunk and aggregate the scores
- More data validation to see if we can chunk transcripts into Q&A pairs - split majority using <strong> tags (~93%), 33 (~7%) don't and it mostly editorial content. Out decision is to process with <strong> tag chunking for the majority and ignore edge cases for now
- ~7% is small enough that it should not skew the sentiment analysis. 
- Tested the baseline model against some basic football quotes -> it performed well with a high confidence level
- Basline model then tested on some rows in our database -> model underperformed on the majority of tests
- Experimented with chunking. HTML body is split into question and answer pairs using the function in `preprocessing/chunking.py`
- The model lacks confidence with quotes that are measured, use diplomatic lanaguage. This is a fundamental domain problem and would require further fine tuning
- Added chunking to the database using nid as a forign key. All together we have 481 transcripts and 6159 chunks. 


#### Key decision
**Decision:** Chose Twitter-RoBERTa-base-sentiment as a baseline model

**Why:** It is pretrained on tweets so it has a strong baseline for informal, emotional text. 

**Alternatives considered:** Considered using DistilBERT or other popular sentiment analysis models on hugging face

**Trade-offs:** Tweets are people expressing opinions and emotions directly, whilst press conferences are managers giving carefully considered, media-trained repsonses. The sentiment may be a little bit harder to extract. 

**Open questions:**
- How well will the baseline model perform on our data
- Will we have to fine-tune our model and how will be go about training or getting labled data. 

**Interview Q I should be able to answer:** 
- Why did you choose that model as your baseline model? 


--- 

#### Key decision
**Decision:** Selected Twitter-RoBERTa-base-sentiment over DistilRoberta-financial-sentiment to move forward as baseline model

**Why:** The financial model displayed overconfidence in its results. Twitter-RoBERTa, although incorrect, displayed signals or uncertainty in its incorrect results, which is more telling. 

**Alternatives considered:** Considered using DistilRoberta-financial-sentiment

**Trade-offs:** The model still struggles with the same type of text - measured, media-trained langauge, where a manager is putting a positive spin on a negative result. This is a fundemental domain problem. 

**Open questions:**
- Is it worth fine-tuning the model to our domain?
- Could we attempt LLM-assisted labelling 
- Is it worth labelling by hand for maximum accuracy?

**Interview Q I should be able to answer:** 
- Twitter-RoBERTa-base-sentiment displays better calibration as its overall confidence reflects the accuracy better. 

--- 

## Phase 4 — Sentiment Analysis Pipeline

### 2026-03-23 

#### What I did
 - Built sentiment pipeline in `src/nlp/sentiment.py`
 - Added label and score columns to chunks table
 - Ran inference on al 6159 chunks: computed score and label by running out baseline model for every answer in the chunks table
 - The baseline model systematically underdetects negative sentiment in football press conferences, returning only 9% negative labels. This is consitent with the domain mismatch hypothesis - diplomatic-trained langauge is misclassified as neutral of positive

## Phase 5 — Embeddings
- Generated embeddings for all chunks in `src/embeddings/generate_embeddings.py`
- Used sentence-transformer "all-MiniLM-L6-v2" to generate the embeddings 
- Genereated 384-dimensional embeddings for all 6159 chunks
- Normalised embeddings for cosine similarity
- Build a FAISS IndexFlatIP index
- Saved the index to `data/processed/chunks.faiss`
- Saved the chunk ID mapping to `data/processed/chunk_ids.json`

---

#### Key decision
**Decision:** Selected all_MiniLM-L6-v2 as our sentence transformer

**Why:** The model has 206M downloads on Huggingface, making is trsutworthy. It is fast and good quality (384-dim) 

**Alternatives considered:** Various other Huggingface models

**Trade-offs:** It is a distilled, smaller model. Larger models like all-mpnet-base-v2 produce better embeddings but are slower and heavier. Fewer dimensions means faster search but potentially less expensive representation. 

**Open questions:**
- Does the retrieval actually work?
- How many chunks should we retrieve per query (k=3?, k=5?)
- Does it handle football-specific terminology well, or does it suffer the same domain problem as the sentiment model?

**Interview Q I should be able to answer:** 
- Why did you chose all-MiniLM-L6-v2 as your sentence transformer?  

--- 