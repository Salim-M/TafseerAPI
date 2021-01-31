from flask import Flask, request, g
import requests as r
from bs4 import BeautifulSoup
import json
import sqlite3

# TODO:
# Check if surah and ayah numbers are correct to crawl

app = Flask(__name__)

DATABASE = "tafseer_database.db"

# Create tafseer table if it doesn't exit

conn = sqlite3.connect(DATABASE)
conn.execute('CREATE TABLE IF NOT EXISTS tafseer (ayahNumber TEXT, surahNumber TEXT, surah TEXT, ayah TEXT, tafseer TEXT)')
conn.close()


# api/v1/

@app.route('/', methods=['GET'])
def home():
    return {
        "name" : "Tafseer API",
        "author" : "Salim Majzoub",
        "version" : "v1"
    }

@app.route('/api/v1/tafseer', methods=['GET'])
def tafseer():
    ayah = request.args.get('ayah')
    surah = request.args.get('surah')

    # Check
    if surah is None or ayah is None:
        return "Bad Request", 400

    # ayah in quran, not in surah

    # 1) Check if tafseer is in the db
    # 1.1) True -> return JSON Object
    # 1.2) False -> Crawl Tafseer, Insert in DB, return JSON Object

    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute("SELECT * FROM tafseer WHERE ayahNumber='%s' AND surahNumber='%s'" % (ayah, surah))
    row = cur.fetchone()

    if row is None:
        # Crawl
        url = "https://equran.me/tafseer-{ayah}-{surah}.html".format(ayah = ayah, surah = surah)
        page = r.get(url, headers= {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
        })
        soup = BeautifulSoup(page.content, 'html.parser')

        surahTEXT = soup.find('div', attrs={"class": ["infoSurat", "one"]}).findChildren("h2", recursive=False)[0].getText()
        ayahTEXT = soup.find('div', attrs={"class": "tafseer"}).findChildren("h2", recursive=False)[0].getText()
        
        titles = soup.find('div', attrs={"class": "tafseer"}).findAll('h3')[1:]
        paraghraphs = soup.find('div', attrs={"class": "tafseer"}).findAll('p')[1:]
        
        data = []

        for title, paraghraph in zip(titles, paraghraphs):
            data.append({
                "type": title.getText(),
                "body": paraghraph.getText()
            })
        # Put in DB
        cur.execute("INSERT INTO tafseer (ayahNumber,surahNumber,surah,ayah,tafseer) VALUES (?,?,?,?,?)", (ayah,surah,surahTEXT,ayahTEXT,json.dumps(data))) 
        con.commit()
        # return JSON Object
        return {
            "ayah": ayahTEXT,
            "surah": surahTEXT,
            "method": "crawler",
            "results": data
        }
    # return JSON Object
    return {
        "ayah": row[3],
        "surah": row[2],
        "method": "database",
        "results": json.loads(row[4])
    }