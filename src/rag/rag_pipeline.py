import sqlite3
from groq import Groq
import faiss
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import json
import os
import numpy as np

# Load API key
load_dotenv()
groq_api_key = os.getenv("GROQ_API")
# Clinet object calls the LLM
client = Groq(api_key=groq_api_key)

# load chunk_ids
with open('data/processed/chunk_ids.json', 'r') as f:
    chunk_ids = json.load(f)

# load faiss index
index = faiss.read_index('data/processed/chunks.faiss')

#load model
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')



def retrieve_chunks(query, k=5):
    """
    Embeds the query, normalises the embedding,
    searches the FAISS index 
    Args:
        query, k
    Returns:
        Top k chunk IDS
    """
    embeded = model.encode(query) # returns 1D array
    embeded = embeded[np.newaxis, :] # reshape for faiss
    faiss.normalize_L2(embeded) 
    dist, indices = index.search(embeded, k)
    flat_indices = indices.flatten() # flatten for chunk ids
    return [chunk_ids[i] for i in flat_indices]



def get_chunk_text(chunk_ids):
    """
    Takes top k chunk ids and returns associated answer
    Args:
        Chunk indices
    Returns:
        Chunk answer text as a list
    """
    # connect to the database
    con = sqlite3.connect('data/database.db')
    cur = con.cursor()
    chunk_text = []
    for chunk_id in chunk_ids:
        cur.execute("SELECT answer FROM chunks WHERE id = ?", (chunk_id,)) # SQL Query expects a tuple
        chunk_text.append(cur.fetchone()[0]) # index 0 to return strong not tuple
    return chunk_text
    


def build_prompt(query, chunk_texts):
    system = f"""You are a football analysis expert specialising in Arsenal press conferences. 
Answer the question using only the context provided below. 
Do not use any outside knowledge in your response.""" + "\n\n"

    user = "Context:" + "\n\n".join(chunk_texts) + "\n\n" + f"Question: {query}"

    return system, user


def generate_answer(system, user):
    """
    Generates the LLM response using Groq API
    Args:
        system (string), user (string)
    Returns:
        Generated response as a string
    """
    chat_completion = client.chat.completions.create(
        messages= [
            {
                "role" : "system",
                "content" : system
            },
            {
                "role" : "user",
                "content" : user
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content



def rag_query(query):
    """
    Full RAG pipeline
    Args:
        query (string)
    Returns
        answer
    
    """
    chunk_ids = retrieve_chunks(query)
    chunk_text = get_chunk_text(chunk_ids)
    system, user = build_prompt(query, chunk_text)
    answer = generate_answer(system, user)
    return answer, chunk_text




