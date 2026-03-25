import sqlite3
import torch
from transformers import pipeline


# import model
model = f"cardiffnlp/twitter-roberta-base-sentiment-latest"
model_baseline = pipeline("sentiment-analysis", model=model, truncation=True, max_length=512)

# connect to the datatbase
conn = sqlite3.connect("/Users/shakurahmad/PythonProjects/pl-press-conference-analyser/data/database.db")
cur = conn.cursor()

def chunk_score(id, score,label,cur):
    cur.execute("UPDATE chunks SET label = ?, score = ? WHERE id = ?",
                 (label, score, id))


cur.execute("SELECT answer, id FROM chunks")
rows = cur.fetchall()

for answer, chunk_id in rows:
    model_result = model_baseline(answer)
    score = model_result[0]['score']
    label = model_result[0]['label']
    chunk_score(chunk_id, score, label, cur)
conn.commit()

