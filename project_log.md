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
- Does the `body` field always contain the full transcript, or sometimes just a summary? - some of the files contain other information or general articles so will have to be filtered
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

**Trade-offs:** CSV files can be opened in Excel or viewed directly, SQLite requires a tool or code to inspect. We also lose some simplicity (setting up connections, cursors...)

**Open questions:**
- Does the cleaned body text still contain any unwanted content beyond <a> tags?
- Does querying the database work? 


**Interview Q I should be able to answer:** 
- Why did you use SQLite over a proper database like PostgreSQL? SQLIte is severless and file based - no setup, no separate process, perfect for a project this size. PostgreSQL is for multi-user, high-concurrent systems.
- Walk me though your HTML cleaning process - why did you specifically remove <a> tags, and what else might you have missed? We used beautiful soup to clean the HTML. find_all was used to find all the text with the HTML link tag <a> and then .decompose to remove it from the body. There might still be text that is not links but filler information or introductions. 
- Your created field is stored as a Unix timestamp. How would you query all press conferences from 2023? SELECT * FROM arsenal WHERE created BETWEEN 1672531200 AND 1704067199. We can use datetime module for conversions. 

--- 

## Phase 3 — Selecting and Testing a Baseline Model

### 2026-03-24

#### What I did
- Searched hugging face for sentiment analysis model
- Also checked for any football or sports related ones -> No reliable ones were found
- Selected Twitter-RoBERTa-base-sentiment as a baseline model
- Model has a 512 token limit so we will chunk transcripts into sections, analyse each chunk and aggregate the scores
- More data validation to see if we can chunk transcripts into Q&A pairs - split majority using <strong> tags (~93%), 33 (~7%) don't and it mostly editorial content. Our decision is to process with <strong> tag chunking for the majority and ignore edge cases for now
- ~7% is small enough that it should not skew the sentiment analysis. 
- Tested the baseline model against some basic football quotes -> it performed well with a high confidence level
- Baseline model then tested on some rows in our database -> model underperformed on the majority of tests
- Experimented with chunking. HTML body is split into question and answer pairs using the function in `preprocessing/chunking.py`
- The model lacks confidence with quotes that are measured, use diplomatic language. This is a fundamental domain problem and would require further fine tuning
- Added chunking to the database using nid as a foreign key. All together we have 481 transcripts and 6159 chunks.


#### Key decision
**Decision:** Chose Twitter-RoBERTa-base-sentiment as a baseline model

**Why:** It is pretrained on tweets so it has a strong baseline for informal, emotional text. 

**Alternatives considered:** Considered using DistilBERT or other popular sentiment analysis models on hugging face

**Trade-offs:** Tweets are people expressing opinions and emotions directly, whilst press conferences are managers giving carefully considered, media-trained responses. The sentiment may be a little bit harder to extract. 

**Open questions:**
- How well will the baseline model perform on our data
- Will we have to fine-tune our model and how will be go about training or getting labelled data. 

**Interview Q I should be able to answer:** 
- Why did you choose that model as your baseline model? 


--- 

#### Key decision
**Decision:** Selected Twitter-RoBERTa-base-sentiment over DistilRoberta-financial-sentiment to move forward as baseline model

**Why:** The financial model displayed overconfidence in its results. Twitter-RoBERTa, although incorrect, displayed signals or uncertainty in its incorrect results, which is more telling. 

**Alternatives considered:** Considered using DistilRoberta-financial-sentiment

**Trade-offs:** The model still struggles with the same type of text - measured, media-trained language, where a manager is putting a positive spin on a negative result. This is a fundamental domain problem. 

**Open questions:**
- Is it worth fine-tuning the model to our domain?
- Could we attempt LLM-assisted labelling 
- Is it worth labelling by hand for maximum accuracy?

**Interview Q I should be able to answer:** 
- Twitter-RoBERTa-base-sentiment displays better calibration as its overall confidence reflects the accuracy better. 

--- 

## Phase 4 — Sentiment Analysis Pipeline

### 2026-03-25

#### What I did
 - Built sentiment pipeline in `src/nlp/sentiment.py`
 - Added label and score columns to chunks table
 - Ran inference on all 6159 chunks: computed score and label by running our baseline model for every answer in the chunks table
 - The baseline model systematically underdetects negative sentiment in football press conferences, returning only 9% negative labels. This is consistent with the domain mismatch hypothesis - diplomatic-trained language is misclassified as neutral or positive

 #### Key decision
**Decision:** Ran sentiment on chunks rather than on whole transcripts

**Why:** Transcripts exceed the 512 token limit, so chunking was necessary to avoid truncation. Also, sentiment per Q&A pair is more meaningful than one score for a whole transcript. Managers can be positive and negative about different questions in the same conference. 

**Alternatives considered:** Truncate the transcripts and lose valuable context from the data

**Trade-offs:**  
- Storage/computation trade/off. Create another table in our database with around 6000 elements
- Lose context of the conference as a whole. A manager's sentiment may shift throughout the conference, so we miss that narrative. Also, short answers lose context without surrounding transcript. 

**Open questions:**
- How do we aggregate chunk-level sentiment scores into a transcript-level score? Average? Weighted?
- Should short answers be excluded from sentiment score? 
- How do we handle the bleeding issue - does it affect sentiment score? 

**Interview Q I should be able to answer:** 
- Why did you chose to split conferences in Q&A pairs, rather then encoding the transcripts as a whole? 

---
## Phase 5 — Embeddings

### 2026-03-25

#### What I did
- Generated embeddings for all chunks in `src/embeddings/generate_embeddings.py`
- Used sentence-transformer "all-MiniLM-L6-v2" to generate the embeddings 
- Generated 384-dimensional embeddings for all 6159 chunks
- Normalised embeddings for cosine similarity
- Built a FAISS IndexFlatIP index
- Saved the index to `data/processed/chunks.faiss`
- Saved the chunk ID mapping to `data/processed/chunk_ids.json`

---

#### Key decision
**Decision:** Selected all_MiniLM-L6-v2 as our sentence transformer

**Why:** The model has 206M downloads on Huggingface, making it trustworthy. It is fast and good quality (384-dim) 

**Alternatives considered:** all-mpnet-base-v2 (higher quality but slower and larger) and text-embedding-ada-002 (Best quality but costs money per API call)

**Trade-offs:** It is a distilled, smaller model. Larger models like all-mpnet-base-v2 produce better embeddings but are slower and heavier. Fewer dimensions means faster search but potentially less expressive representation. 

**Open questions:**
- Does the retrieval actually work?
- How many chunks should we retrieve per query (k=3?, k=5?)
- Does it handle football-specific terminology well, or does it suffer the same domain problem as the sentiment model?

**Interview Q I should be able to answer:** 
- Why did you chose all-MiniLM-L6-v2 as your sentence transformer?  

--- 

## Phase 6 — Build RAG Pipeline

### 2026-03-26

### What RAG does:
1. A function that takes a user's question and retrieves the most relevant chunks from FAISS
2. A function that constructs a prompt from those chunks and the question 
3. A call to Groq to generate the answer

#### What I did
- Went to console.groq.com to create an API key before building
- Plan the RAG pipeline: Get chunk ids -> get chunk text -> build prompt -> generate answer
- Created the function to retrieve chunks: Embeds the query, normalises the embedding, searches the FAISS index and returns the chunk indices
- Created the function to collect associated text from chunk ids
- Created the function to build the prompt to sent to Groq. Consisting of system constraints and user query
- Created the function to generate Groq response
- Full pipeline tested on simple self-generated prompts


#### Key decision
**Decision:** Selected Groq with llama 3.3 70B to use as response generator

**Why:** Groq provides a free tier which uses a fast LPU (language processing unit -> designed for running LLMs fast) interface. 70B parameters gives good quality. 

**Alternatives considered:** OpenAI GPT-4 (best quality but costs money), Ollama (local LLM, free but requires significant compute and RAM), HuggingFace Inference API (free tier but rate limited and slower)

**Trade-offs:** 
- Free tier has rate limits if traffic
- Dependent on an external API - if Groq goes down, app stops working
- Llama is powerful but not fine-tuned on football - same domain problems

#### Key decision
**Decision:** k=5 chunks retrieved 

**Why:** So far, the decision is not fully justified. This should be tested systematically (RAGAS). However too few chunks risks missing relevant context and too many chunks risks diluting the prompt with irrelevant content. Therefore, k=5 is a resonable default. 

**Alternatives considered:** No alternatives considered at the moment but consider 3, 10 ect...

**Trade-offs:** 
- Possibly too few chunks -> Fast, focused prompt but risk of missing relevant context that is spread across multiple Q&A pairs
- Possibly too many chunks -> More context but slower retrieval and generation. Risk of inclusing irrelevant chunks

**Interview Q I should be able to answer:** 
- Why did you select k=5 nearest chunks for retrival?
- Why did you choose to use Groq as your LLM to generate responses? 

## Phase 7 — Flask App

### 2026-03-27

# Notes: 
- GET — sends data in the URL, e.g. localhost:5000/chat?query=what+did+Arteta+say. Visible in the browser, bookmarkable, but has length limits.                          
- POST — sends data in the request body, not the URL. Better for longer text inputs, and more appropriate when you're sending data to be processed. 

#### What I did
- Planned the app - twp pages: sentiment dsahbaord and RAG chat
- Created `src/app/` folder structure (`templates/`, `static/`, `app.py`)
- Built minimal Flask app with a `/` route returning "hello world"
- Created `dashboard.html` template and connected it via `render_template`
- Write get_data() function - queries SQLite with a JOIN between arsenal and chunks, computes weighted sentiment per conference, converted Unix timestamps to readable dates
- Fixed threading error - moved database connection inside get_data()
- Passed dates and scores to template via Jinja2, rendered sentiment timeline with Chart.js
- Wrote distribution query - counts positive/neutral/negative chunks per year using strftime to extract year from Unix timestamp
- Created `chat.html` template and connected it via `render_template`
- Added the <textarea> and submit button that lets users type a question
- Added the form with POST method 
- Updated `/chat` route to handle GET and POST
- Integrated rag_query() into the route
- Displayed the answer in the template
- Modified rag_query() to return chunk texts alongside the answer
- Added collapsible source citations using <details>

#### Key decision
**Decision:** Used a weighted average for sentiment scores 

**Why:** So that scores with low confidence scores are not over represented in the overall transcript result. Scores that are possible incorrect could decrease accuracy. 

**Alternatives considered:** Plain average of all sentiment scores across chunk labels

**Trade-offs:** 
- If the model is overconfident then we have given higher weight to incorrect results
- Plain average is simpler and easier to exaplin - weighted averages adds complexity


**Interview Q I should be able to answer:** 
- Why did you use a weighted average instead of a simple average for your sentiment scores?
- What assumptions does your weighting scheme make about the model's confidence scores?

---

#### Key decision

**Decision:** Used chunk labels for the distribution chart instead of weighted scores 

**Why:** Chunk labels are simpler, consistent with the model's output, and sufficient for showing distribution trends

**Alternatives considered:** Using the weighted average scores to re-label the transcripts as a whole 

**Trade-offs:** 
- We are trusting the model's label even when its confidence is low

--- 

#### Key decision

**Decision:** Used POST method on the form

**Why:** Query text should not appear in the URL and it is better for long inputs

**Alternatives considered:** GET method

**Trade-offs:** 
- Users will not be able to bookmark, share of paste URL. GET gives you shareable, bookmarkeable URLs, POST doesn't. For a chat interface the query is often long and one-time so bookmarking is not useful

**Interview Q I should be able to answer:** 
- Why did you choose to use POST method on the form?
- What is the difference between POST and GET

---

#### Key decision

**Decision:** Used collapsible citations 

**Why:** It makes the RAG mechanics transparent to a hiring manager. They can see exactly what the context the model used to generate the answer.

**Alternatives considered:** Providing the full chunk texts on the page without being collapsible 

**Trade-offs:** 
- Hidden citations might mean users never open them - so transparency benefit only works if users actually click.

**Interview Q I should be able to answer:** 
- Why did you choose to provide the chunk citations on the page?

---

## Phase 8 — Deployment
### 2026-03-28

#### What I did
- Created Procfile for Render to read
- Used gunicorn for proper deployment 
- Procfile run line: `gunicorn src.app.app:app` -> tells Render where to run 
- Removed faiss version in requirements.txt to avoid Render deployment mismatch
- Removed `database.db` and `data/processed` from `.gitignore` so Render has acess to the data
- Added `.python-version` to pin python version in Render
- Created a new web service in Render (free version)
- Added Groq API key to render enviroment variables
- Fix Procfile: use gunicorn with correct port binding for Render (` --bind 0.0.0.0:$PORT`)

### Hit deployment problems -> memory constraints on free tier -> Deployment deferred to focus on improving the project

---

## Phase 9 - Styling
### 2026-03-28
- Created `base.html` for shared features across pages
- Created a plan for a basic theme -> navy and sports dashboard vibe
- Made the plan into a prompt for Claude and ChatGPT to provide the `base.html` code
- The AI prompt is pasted in a small changes were made to the "ask" button on the RAG chat page

---

#### Key decision

**Decision:** Used Cluade and ChatGPT to assist with page styling

**Why:** Creating nice looking pages is not the focus of this project. Time should be put into the understanding of more ML areas of the project. Also, Claude does a very good job at tasks like this.  

**Alternatives considered:** Writing all html without the use of AI

**Trade-offs:** 
- HTML and wepage styling skills are not devloped or pushed further
- Less customisability and control -> Claude makes a lot of minor decisions and requires tweaking

**Interview Q I should be able to answer:** 
- Why did you feel that it was appropriate to let an AI model handle the app page design? 

