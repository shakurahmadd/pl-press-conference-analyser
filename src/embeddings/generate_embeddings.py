import sqlite3
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import json

#import sentence-transformer model
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# connect to the database
con = sqlite3.connect('/Users/shakurahmad/PythonProjects/pl-press-conference-analyser/data/database.db')
cur = con.cursor()


cur.execute("SELECT id, answer FROM chunks")
rows = cur.fetchall()
id_list = []
answer_list = []
for id_, answer in rows:
    id_list.append(id_)
    answer_list.append(answer)

# generate embeddings for all answers
embeddings = model.encode(answer_list)
print(embeddings.shape)

# normalise the embeddings - cosine similary 
faiss.normalize_L2(embeddings)

index = faiss.IndexFlatIP(384) # cosine similarity (dim 384)
index.add(embeddings)

# The FAISS index saved as .faiss file
faiss.write_index(index,'data/processed/chunks.faiss' )

#id_list (mapping FAISS positions to database chunk IDS) as .json
with open("data/processed/chunk_ids.json", "w") as f:
    json.dump(id_list, f)
