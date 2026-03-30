import sqlite3
from os import listdir
import json
from bs4 import BeautifulSoup
import sys
sys.path.append('/Users/shakurahmad/PythonProjects/pl-press-conference-analyser')
from src.preprocessing.chunking import chunk_by_qa





def clean_body(html):
    """
    Cleans the html transcripts
    Args: 
        html data (document['body'])
    Returns:
        html txt
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all('a'): # we remove html links from the text
        tag.decompose()

    return soup.get_text(separator=" ", strip=True)
     

def insert_into_db(document, cur):
    """
    Sends the data from document into the database
    Args:
        document (json file), cur
    Returns:
        None
    """
    cleaned = clean_body(document['body']) # Insert or ignore so we can run it again
    cur.execute("""
        INSERT OR IGNORE INTO arsenal 
                (nid, created, title, url, body, raw_body)
                 VALUES (?, ?, ?, ?, ?, ?)""", 
                 (document['nid'], document['created'], 
                  document['title'], document['url'], cleaned, document['body']))
    


def intert_into_chunks(nid, question, answer,cur):
    cur.execute("""
        INSERT OR IGNORE INTO chunks
                (nid, question, answer)
                VALUES (?, ?, ?)""",
                 (nid, question, answer))



if __name__ == "__main__":
    path = '/Users/shakurahmad/PythonProjects/pl-press-conference-analyser/data/raw'
    file_names = listdir(path)

    con = sqlite3.connect("data/database.db")
    cur = con.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS arsenal(
                nid INTEGER PRIMARY KEY,
                created INTEGER,
                title TEXT,
                url TEXT,
                body TEXT,
                raw_body TEXT)""")
    con.commit()

    cur.execute("""CREATE TABLE IF NOT EXISTS chunks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nid INTEGER,
                question TEXT,
                answer TEXT,
                UNIQUE(nid, question))""")
    con.commit()

    for file in file_names:
        if file.endswith(".json"):
            with open(f"{path}/{file}") as f:
                document = json.load(f)
                if len(document['body'].split()) > 200:
                    insert_into_db(document, cur)
                    con.commit()

    cur.execute("SELECT nid, raw_body FROM arsenal")
    rows = cur.fetchall()
    for row in rows:
        chunks = chunk_by_qa(row[1])
        for chunk in chunks:
            intert_into_chunks(row[0], chunk['question'], chunk['answer'], cur)
            con.commit()

    cur.execute("SELECT COUNT(*) FROM arsenal")
    print(cur.fetchone())

    cur.execute("SELECT COUNT(*) FROM chunks")
    print(cur.fetchone())

    cur.execute("SELECT * FROM chunks LIMIT 1")
    print(cur.fetchall())

    con.close()



