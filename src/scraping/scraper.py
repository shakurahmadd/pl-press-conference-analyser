import requests
import os
from dotenv import load_dotenv
import time
import json

load_dotenv()

api_key = os.getenv("API_KEY")  # API key safely stored in env

url = f'https://govzt6l7e4ci9pm0p-1.a1.typesense.net/multi_search?x-typesense-api-key={api_key}'

def get_articles(page_num):
    """
    Send request and grabs hits
    Args: 
        page_num: page number to fetch from
    Returns:
        article hits as a dictionary
    """
    payload = {
        "searches": [
            {
                "query_by": "title,body,category_name",
                "sort_by": "_text_match:desc,created:desc",
                "highlight_full_fields": "",
                "filter_by": "arsenal_team:=[`Men`] && category_name:=[`Press conference`]", # added press conference filter
                "query_by_weights": "3,2,1",
                "collection": "news_and_articles",
                "q": "Every word",
                "facet_by": "arsenal_team",
                "max_facet_values": 10,
                "page": page_num,
                "per_page": 250
            }
        ]
    }

    request = requests.post(url=url, json=payload)
    if request.status_code != 200:  # if it is unable to connect
        print(f"Scraping failed on page: {page_num}")
    data = request.json()   
    return data['results'][0]['hits']


def save_article_as_json(document):
    """
    Takes Python dictionary and saves it as a JSON file to data folder
    Args:
        document: article nid, title, url, body
    Returns: 
        None
    """
    with open(f"data/raw/{document['nid']}.json", 'w') as file:
        json.dump(document, file)


for page_num in range(1, 4):    # search 3 pages
    hits = get_articles(page_num)
    for hit in hits:
        save_article_as_json(hit['document']) 
    time.sleep(10)      # delay to not exceed rate limit 

