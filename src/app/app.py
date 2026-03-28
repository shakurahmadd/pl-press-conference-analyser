from flask import Flask, render_template, request
import sqlite3
import os
from datetime import datetime 
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.rag.rag_pipeline import rag_query



# create instance of of class 
# __name__ refers to the current file
app = Flask(__name__)

# "/" site root
@app.route('/')
def dashboard():
    dates, scores = get_data()
    years, positive_ratio, neutral_ratio, negative_ratio = get_distribution()
    return render_template("dashboard.html", dates=dates, scores=scores, years=years, 
                           neutral_ratio=neutral_ratio, positive_ratio=positive_ratio, negative_ratio= negative_ratio)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        query = request.form['query']
        answer, chunks = rag_query(query)
        return render_template('chat.html', answer = answer, chunks=chunks)
    else:
        return render_template('chat.html')



def get_data():
    con = sqlite3.connect('data/database.db')
    cur = con.cursor()
    cur.execute("""SELECT created, title, AVG(score * CASE WHEN label = 'positive' THEN 1 WHEN label = 'negative' THEN -1 ELSE 0 END)
                 AS weighted_sum FROM chunks JOIN arsenal ON chunks.nid = arsenal.nid GROUP BY arsenal.nid""")
    query_data = cur.fetchall()
    
    data = [[datetime.strftime(datetime.fromtimestamp(data_tuple[0]), "%Y-%m-%d"),
              data_tuple[1], data_tuple[2]] for data_tuple in query_data]
    
    dates = [date[0] for date in data]
    scores = [score[2] for score in data]

    return dates, scores


def get_distribution():
    con = sqlite3.connect('data/database.db')
    cur = con.cursor()
    cur.execute("""SELECT strftime('%Y', datetime(created, 'unixepoch')),
                 COUNT(CASE WHEN label = 'positive' THEN 1 END),
                COUNT(CASE WHEN label = 'neutral' THEN 1 END),
                COUNT(CASE WHEN label = 'negative' THEN 1 END) 
                FROM arsenal JOIN chunks ON chunks.nid = arsenal.nid GROUP BY
                strftime('%Y', datetime(created, 'unixepoch'))""")
    distribution = cur.fetchall()
    years = [dist_tuple[0] for dist_tuple in distribution] 
    positive_ratio = [(dist_tuple[1] / (dist_tuple[1] + dist_tuple[2] + dist_tuple[3])) for dist_tuple in distribution] 
    neutral_ratio = [(dist_tuple[2] / (dist_tuple[1] + dist_tuple[2] + dist_tuple[3])) for dist_tuple in distribution] 
    negative_ratio = [(dist_tuple[3] / (dist_tuple[1] + dist_tuple[2] + dist_tuple[3])) for dist_tuple in distribution] 
    return years, positive_ratio, neutral_ratio, negative_ratio



# runs only if execute the file directly
if __name__ == "__main__":
    app.run(debug=True)

