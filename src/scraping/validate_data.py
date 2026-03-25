from os import listdir
import json
from bs4 import BeautifulSoup

path = '/Users/shakurahmad/PythonProjects/pl-press-conference-analyser/data/raw'

file_names = listdir(path)
empty_bodycount = 0
bodies = []
low_word_titles = []
soup_count = 0
soup_titles = []
soup_br_count = 0
soup_br = []
for file in file_names:
    if file.endswith(".json"):
        with open(f"{path}/{file}") as f:
            data = json.load(f)
            if len(data['body']) == 0:
                print(f"file: {file} has no body")
                empty_bodycount += 1    
            if len(data['body'].split()) < 200:
                print(f"{file} has {len(data['body'].split())} words")
                low_word_titles.append(data['title'])
            soup = BeautifulSoup(data['body'], 'html.parser')
            if soup.find('strong'):
                soup_count += 1
            else:
                soup_titles.append([data['title'], data['nid']])

            if soup.find('br') and not soup.find('strong'):
                soup_br_count += 1
                soup_br.append([data['title'], data['nid']])


            bodies.append(len(data['body'].split()))

            
        
print(f"The number of files with empty transcripts is: {empty_bodycount}")
print(f"The number of words in the largest trascript is: {max(bodies)}")
print(f"The number of words in the smallest trascript is: {min(bodies)}")
print(f"The average word count in the trascripts is: {sum(bodies) / len(bodies)}")
print(low_word_titles)
print('Strong tag count:',soup_count)
print('Strong tag [titles: nid]', soup_titles)
print('Br tag count:',soup_br_count)
print('Br tag [titles: nid]', soup_br)
