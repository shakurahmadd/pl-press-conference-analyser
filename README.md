# PL Press Conference Analyser

A natural language processing system that analyses Premier League manager press conference transcripts. It tracks sentiment trends over time using a pre-trained RoBERTa model, and provides a RAG-powered chat interface where users can ask questions and receive answers grounded in real transcript data.

## What it does

Press conference transcripts contain valuable insights but are rarely analysed systematically. This tool lets football fans and analysts track how a manager's tone and sentiment shifts over time, and query a chat interface to find specific information — grounded in the manager's own words, not hallucinated.

## Tech Stack

| Tool | Role |
|------|------|
| Python | Core language |
| SQLite | Stores scraped transcripts and sentiment scores |
| Twitter-RoBERTa | Sentiment analysis on Q&A chunks |
| Sentence Transformers (all-MiniLM-L6-v2) | Encodes queries and chunks into vector embeddings |
| FAISS | Vector index for fast semantic similarity search |
| Groq / Llama 3.3 70B | LLM for generating grounded answers |
| Flask | Web framework serving the dashboard and chat interface |
| Chart.js | Sentiment trend visualisation |
| BeautifulSoup | HTML cleaning and Q&A chunking |
| Requests | Scraping Arsenal's Typesense API |

## Architecture

```
Arsenal Typesense API → Raw JSON → SQLite
                                      ↓
                          BeautifulSoup Q&A chunking
                                      ↓
                    Twitter-RoBERTa sentiment scoring
                                      ↓
                    Sentence Transformer embeddings → FAISS index
                                      ↓
                         Flask app (Dashboard + RAG Chat)
                                      ↓
                              Groq / Llama 3.3 70B
```

## Getting Started

```bash
# Clone the repo
git clone <https://github.com/shakurahmadd/pl-press-conference-analyser>
cd pl-press-conference-analyser

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your GROQ_API key

# Run the app
python src/app/app.py
```

## Known Limitations

- **Domain mismatch:** The sentiment model was trained on tweets, not football press conferences. Diplomatic, media-trained language is systematically misclassified — negative sentiment is underdetected (~9% vs an expected ~25-35%).
- **Arsenal only:** Currently covers Arsenal press conferences from January 2018 to March 2026.

## Future Work

- Expand to all Premier League clubs
- Fine-tune sentiment model on labelled football press conference data
- Add player-level sentiment filtering
- Improve RAG retrieval with better chunking strategy
