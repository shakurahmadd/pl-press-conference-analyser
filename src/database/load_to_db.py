import sqlite3
from os import listdir
import json
from bs4 import BeautifulSoup

path = '/Users/shakurahmad/PythonProjects/pl-press-conference-analyser/data/raw'


file_names = listdir(path) # gives a list of all the files in directory

con = sqlite3.connect("data/database.db")
cur = con.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS arsenal(
            nid INTEGER PRIMARY KEY, 
            created INTEGER,
            title TEXT,
            url TEXT,
            body TEXT)""")

con.commit()

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
                (nid, created, title, url, body)
                 VALUES (?, ?, ?, ?, ?)""", 
                 (document['nid'], document['created'], 
                  document['title'], document['url'], cleaned))


for file in file_names:
    if file.endswith(".json"):
        with open(f"{path}/{file}") as f:
            document = json.load(f)
            if len(document['body'].split()) > 200: # word count threshold
                insert_into_db(document, cur) 
                con.commit()


cur.execute("SELECT COUNT(*) FROM arsenal")     
print(cur.fetchone())
con.close()


